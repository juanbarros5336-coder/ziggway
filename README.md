# Projeto de Análise de E-commerce com IA

Link do projeto https://ziggway.streamlit.app/, para iniciar clique no botão azul e aguarde o carregamento 😊

Este projeto utiliza Análise de Dados e integração com APIs de Inteligência Artificial para processar dados de vendas e analisar comentários de clientes, ajudando a identificar problemas na operação de uma loja.

## Sobre o Projeto

O sistema resolve um problema comum: a dificuldade de analisar grandes volumes de feedback de clientes.
A aplicação processa dados do dataset público da Olist e oferece:

1. Visão Estratégica: Métricas financeiras, ticket médio e evolução de vendas.
2. Análise de Sentimento: Uso de IA para ler comentários, identificar sentimento (positivo/negativo) e classificar a urgência de cada caso.

## Tecnologias Utilizadas

- Python 3.10+
- Streamlit 
- Pandas 
- Groq API / DeepSeek 
- Plotly 

## Estrutura do Projeto

O código está organizado em módulos para facilitar a manutenção:
Visão Estratégica: Painel com os indicadores principais da loja.
CX Command Center: Área dedicada à análise qualitativa. Inclui uma tabela interativa que permite enviar lotes de comentários para análise da IA e receber sugestões de ação.

Como Executar

Para rodar o projeto localmente:

1. Clone este repositório.
2. Instale as dependências listadas no arquivo requirements.txt:
   pip install -r requirements.txt

3. Configure a variável de ambiente com sua chave da Groq API. Crie um arquivo .env na raiz do projeto:
   GROQ_API_KEY=sua_chave_aqui

4. Execute o comando do Streamlit:
   streamlit run app/main.py

## Autor

[Juan Barros](https://github.com/juan-barross/)





