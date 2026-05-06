![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![Microsoft Power BI](https://img.shields.io/badge/Microsoft_Power_BI-F2C811?style=for-the-badge&logo=microsoft-power-bi&logoColor=black)

<img width="1481" height="830" alt="image" src="https://github.com/user-attachments/assets/86f162ea-41a3-4ae0-89e8-da3a82983cfe" />


Um ecossistema completo de dados de um Empório Gourmet, com geração sintética e realista de histórico de vendas para elevar o nível das práticas de SQL, Engenharia de Dados e Business Intelligence. A alternativa definitiva aos bancos de dados "engessados" de cursos.

## 🎯 Objetivo do Projeto
Resolver o problema da escassez de bases de dados volumosas e realistas para estudantes e profissionais de dados. O projeto simula a operação completa de um varejo com **sazonalidade programada** (picos na Black Friday/Dezembro e baixas em Janeiro) e **ciclo de vida logístico real**, permitindo análises complexas, testes de performance de queries e criação de dashboards robustos.

## 🛠️ Stack Tecnológica
- **Engine de Dados:** Python 3.x (Geração de massa de dados sintéticos)
- **Banco de Dados:** SQLite (Estrutura relacional normalizada com 10 tabelas)
- **Consultas & Validação:** SQL (Analytics & Triggers)
- **Visualização & BI:** Microsoft Power BI

## 📂 Arquitetura e Estrutura dos Dados
O banco foi desenhado seguindo modelagem profissional com Chaves Estrangeiras, Constraints e tipos de dados padronizados.
- **Volume:** +40.000 pedidos (Histórico de 2025 e 1º trimestre de 2026).
- **Tabelas Principais:**
  - `Vendas (Orders & Items)`: Faturamento e ticket médio.
  - `Clientes & Endereços`: Dados demográficos e geográficos para mapas de calor.
  - `Categorias & Produtos`: Mix de itens gourmet.
  - `Fornecedores`: Gestão de custos.
  - `Status de Pedidos`: Dimensão isolada para rastreio logístico.
  - `Logs de Auditoria`: Rastreamento de alterações de preços.

## ⚙️ Funcionalidades Avançadas no Motor (Triggers)
Para simular um ambiente de produção blindado contra falhas humanas, o banco opera com 6 automações integradas via script:
1. **Gestão de Estoque Dinâmica:** Baixa automática na venda e estorno no cancelamento.
2. **Soft Delete:** Intercepta `DELETE` na tabela de pedidos, bloqueando a exclusão e alterando o status para 'Canceled'.
3. **Data Cleansing On-the-fly:** Limpeza e padronização instantânea de e-mails de clientes (remoção de espaços e conversão para caixa baixa).
4. **History Log (Auditoria):** Escuta alterações na coluna de preços e grava o histórico "De/Para" em uma tabela isolada.

## 💡 Problemas de Negócio Resolvidos (SQL Analytics)
O repositório inclui o arquivo `queries_analytics.sql` com 12 problemas práticos de negócio resolvidos, prontos para análise:
- **Rentabilidade:** Cálculo de margem unitária por produto.
- **Fidelidade (Retention):** Identificação de clientes recorrentes.
- **Cross-Sell:** Análise de eficiência de carrinho (pedidos de item único).
- **Operação:** Identificação de horários de pico.
- **Logística (Window Functions):** Monitoramento do funil de vendas e distribuição de status.
- **Cancelamentos:** Evolução mensal da taxa de perda (Cancel Rate) via agregação condicional.

## 🚀 Como Executar o Projeto

**Pré-requisitos:** Python 3.x, Ferramenta de Gestão SGBD (DBeaver, SQLite Studio) ou Power BI.

1. **Clone este repositório:**
   
   git clone https://github.com/ruanpmendes/retail-dataset-generator

2. Gere a massa de dados:
   Execute o motor em Python para criar o arquivo emporio_geracoes.db com todo o histórico:

   python main.py
   
4. Conecte e Explore:

   Abra o arquivo .db gerado no DBeaver/SQLite Studio para rodar os desafios do queries_analytics.sql.

   Conecte o banco diretamente ao Power BI para modelar e visualizar as métricas.

🤝 Autor
Ruan Mendes - https://www.linkedin.com/in/ruan--mendes/
   
