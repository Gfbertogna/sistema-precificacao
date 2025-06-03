import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re

PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(PASTA_ATUAL, 'imoveis.csv')

BASE_URL = 'https://www.imobiliariatradicao.com.br'
LISTAGEM_URL = ('https://www.imobiliariatradicao.com.br/Pesquisa/'
                'imoveis-para-venda/tipo-residencial-apartamento+residencial-apartamento-em-condominio-fechado+'
                'residencial-casa+residencial-casa-em-condominio-fechado/p{pagina}/o1/e1')

HEADERS = {'User-Agent': 'Mozilla/5.0'}
LIMITE_IMOVEIS = 10

CAMPOS_CSV = [
    'url', 'tipo', 'objetivo', 'preco',
    'area_util', 'area_total', 'Quartos', 'Banheiros', 'Suites', 'Garagens',
    'Cidade', 'Bairro',
    'Piscina', 'Copa', 'Cozinha',
    'Sala de estar', 'Sala de jantar', 'Sala de visitas'
]


def limpar_texto(texto):
    return re.sub(r'\s+', ' ', texto).strip()

def carregar_links_visitados():
    if not os.path.exists(CSV_FILE):
        return set()
    df = pd.read_csv(CSV_FILE)
    return set(df['url'].dropna().tolist())

def get_links_da_pagina(pagina):
    url = LISTAGEM_URL.format(pagina=pagina)
    print(f'Buscando links na página {pagina}...')
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, 'html.parser')
    links = set()
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/Imovel/' in href:
            link_completo = href if href.startswith('http') else BASE_URL + href
            links.add(link_completo)
    return list(links)

def extrair_detalhes(url):
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, 'html.parser')
    dados = {'url': url}

    h1 = soup.select_one('h1')
    if not h1:
        return None
    texto_h1 = limpar_texto(h1.text).lower()

    # Tipo
    if 'casa' in texto_h1:
        dados['tipo'] = 'Casa'
    elif 'apartamento' in texto_h1:
        dados['tipo'] = 'Apartamento'
    else:
        return None

    # Objetivo
    if 'venda' in texto_h1:
        dados['objetivo'] = 'Venda'
    elif 'locação' in texto_h1 or 'aluguel' in texto_h1:
        dados['objetivo'] = 'locacao'
    else:
        dados['objetivo'] = ''

    # Preço (valor monetário em float)
    preco = soup.select_one('.preco')
    if preco:
        preco_texto = preco.text
        match = re.search(r'[\d\.,]+', preco_texto)
        if match:
            preco_numerico = match.group(0).replace('.', '').replace(',', '.')
            try:
                dados['preco'] = float(preco_numerico)
            except:
                dados['preco'] = ''
        else:
            dados['preco'] = ''
    else:
        dados['preco'] = ''

    # Inicializa campos
    dados.update({
        'area_util': '', 'area_total': '', 'Quartos': '',
        'Banheiros': '', 'Suites': '', 'Garagens': ''
    })

    # Nova abordagem usando a tabela correta (table.v1)
    tabela = soup.select_one('table.v1')
    if tabela:
        for tr in tabela.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) != 2:
                continue
            chave = limpar_texto(tds[0].text).lower()
            valor = limpar_texto(tds[1].text)

            if 'suítes' in chave:
                dados['Suites'] = re.sub(r'\D', '', valor)
            elif 'banheiros' in chave:
                dados['Banheiros'] = re.sub(r'\D', '', valor)
            elif 'área útil' in chave:
                match = re.search(r'[\d.,]+', valor)
                dados['area_util'] = match.group(0).replace('.', '').replace(',', '.') if match else ''
            elif 'área total' in chave:
                match = re.search(r'[\d.,]+', valor)
                dados['area_total'] = match.group(0).replace('.', '').replace(',', '.') if match else ''
            elif 'quartos' in chave or 'dormitórios' in chave:
                dados['Quartos'] = re.sub(r'\D', '', valor)
            elif 'vagas' in chave or 'garagens' in chave or 'vaga' in chave:
                dados['Garagens'] = re.sub(r'\D', '', valor)
            elif 'venda' in chave:
                match = re.search(r'[\d\.,]+', valor)
                if match:
                    valor_numerico = match.group(0).replace('.', '').replace(',', '.')
                    try:
                        dados['preco'] = float(valor_numerico)
                    except:
                        pass

    # Localização
    dados['Cidade'] = ''
    dados['Bairro'] = ''
    local_div = soup.select_one('div.local') or h1.find_next('small')
    if local_div:
        texto_local = limpar_texto(local_div.text)
        partes = [p.strip() for p in texto_local.split('-')]
        if len(partes) >= 2:
            dados['Bairro'] = partes[0]
            dados['Cidade'] = partes[1]
        elif len(partes) == 1:
            dados['Bairro'] = partes[0]

    # Comodidades
    texto_pagina = soup.get_text().lower()
    dados['Piscina'] = 'Sim' if 'piscina' in texto_pagina else 'Não'
    dados['Copa'] = 'Sim' if 'copa' in texto_pagina else 'Não'
    dados['Cozinha'] = 'Sim' if 'cozinha' in texto_pagina else 'Não'
    dados['Sala de estar'] = 'Sim' if 'sala de estar' in texto_pagina else 'Não'
    dados['Sala de jantar'] = 'Sim' if 'sala de jantar' in texto_pagina else 'Não'
    dados['Sala de visitas'] = 'Sim' if 'sala de visitas' in texto_pagina else 'Não'

    return dados


def main():
    visitados = carregar_links_visitados()
    novos_dados = []
    pagina = 1

    while len(novos_dados) < LIMITE_IMOVEIS:
        links = get_links_da_pagina(pagina)
        if not links:
            print(f'Nenhum link encontrado na página {pagina}.')
            break
        for link in links:
            if link in visitados or any(d['url'] == link for d in novos_dados):
                continue
            print('Extraindo:', link)
            try:
                dados = extrair_detalhes(link)
                if dados:
                    novos_dados.append(dados)
                else:
                    print('Imóvel não é casa ou apartamento, ignorado.')
                time.sleep(1)
            except Exception as e:
                print(f'Erro ao extrair {link}: {e}')
            if len(novos_dados) >= LIMITE_IMOVEIS:
                break
        pagina += 1

    if novos_dados:
        df = pd.DataFrame(novos_dados)
        df = df.reindex(columns=CAMPOS_CSV)
        if os.path.exists(CSV_FILE):
            df_existente = pd.read_csv(CSV_FILE)
            df_total = pd.concat([df_existente, df], ignore_index=True)
            df_total.to_csv(CSV_FILE, index=False)
        else:
            df.to_csv(CSV_FILE, index=False)
        print(f'{len(novos_dados)} imóveis salvos no arquivo {CSV_FILE}.')
    else:
        print('Nenhum novo imóvel encontrado.')

if __name__ == '__main__':
    main()
