Este projeto realiza web scraping de dados de imóveis para venda e aluguel, com o objetivo de coletar informações e auxiliar na precificação com base em dados reais do mercado.

Estrutura do Projeto:

.scraper_aluguel.py	Script para coletar dados de imóveis disponíveis para aluguel
.scraper_venda.py	Script para coletar dados de imóveis disponíveis para venda
.imoveis.csv	Arquivo gerado contendo os dados extraídos (endereço, preço, etc.)
.gitignore	Define os arquivos e pastas ignorados pelo Git

Tecnologias Utilizadas

.Python 
.BeautifulSoup / Requests (assumido)
.CSV para armazenamento dos dados

Como Usar:

1. Clone o repositório:
   
git clone https://github.com/Gfbertogna/sistema-precificacao.git
cd sistema-precificacao

2. Instale as dependências

pip install -r requirements.txt

3. Execute o script desejado:

python scraper_venda.py
# ou 
python scraper_aluguel.py

