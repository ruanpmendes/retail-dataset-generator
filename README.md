![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![Microsoft Power BI](https://img.shields.io/badge/Microsoft_Power_BI-F2C811?style=for-the-badge&logo=microsoft-power-bi&logoColor=black)

🍷 Empório das Gerações: Dataset & Data Engineering
Este projeto nasceu para resolver um problema comum entre estudantes de dados: bancos de dados de cursos que são pequenos e "engessados". Aqui, você encontrará um ecossistema completo de um Empório Gourmet, modelado do zero, com um gerador automático de dados em Python que cria um histórico de vendas realista e volumoso para prática de SQL e BI.

🎯 Por que usar este projeto para estudar?
Volume Realista: Chega de tabelas com 10 linhas. O script gera mais de 40.000 pedidos (2025 - 2026(1° trimestre)), permitindo testar a performance de queries e criar dashboards robustos.

Sazonalidade Programada: Os dados não são aleatórios; eles seguem o comportamento do varejo real, com meses de alta (Dezembro/Black Friday) e meses de baixa (Janeiro), ideal para treinar análise de séries temporais.

Modelagem Profissional: Estrutura relacional com 8 tabelas, utilizando Chaves Estrangeiras, Constraints e tipos de dados padronizados.

Foco em BI: Dados gerados com distribuição horária e geográfica para prática de mapas de calor e logística.

🛠️ Tecnologias Utilizadas
Python 3.x: Engine de geração de massa de dados sintéticos.

SQLite: Banco de dados relacional (SQL) portátil e de fácil configuração.

DBeaver: Sugerido para gestão e prototipagem de consultas.

🗂️ Estrutura do Banco de Dados
O banco simula uma operação real de e-commerce/varejo:

Categorias & Produtos: Mix diversificado de itens gourmet.

Fornecedores: Gestão de custos e histórico de compras.

Clientes & Endereços: Localizações variadas para análise de frete e região.

Vendas (Orders & Items): Tabela transacional rica para análise de faturamento e ticket médio.

📊 Desafios de SQL Inclusos
O repositório conta com um arquivo queries_analytics.sql contendo 10 problemas de negócio resolvidos, prontos para serem usados como guia de estudo:

Rentabilidade: Cálculo de margem unitária por produto.

Fidelidade: Identificação de clientes recorrentes (Retention).

Cross-Sell: Análise de eficiência de carrinho (pedidos de item único).

Operação: Identificação de horários de pico (Morning, Afternoon, Evening).

🚀 Como utilizar:
Clone o repositório: Tenha os arquivos em sua máquina.

Gere seus dados: Execute o main.py. Ele criará o arquivo emporio_geracoes.db automaticamente com o histórico de 2025 e 2026.

Conecte e Estude: Abra o arquivo .db em qualquer ferramenta SQL (DBeaver, SQLite Studio) ou conecte-o diretamente ao Power BI / Excel para criar visualizações.

🤝 Contribuição e Propósito
Este projeto é aberto para estudantes e entusiastas de dados. Se você está cansado de praticar com o banco "Northwind" ou "Sakila", este dataset foi feito para você elevar o nível das suas análises.
