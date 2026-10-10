# Parte HTML dos painéis Oracle

Este pacote entrega a estrutura HTML dos 3 painéis já consolidados:

1. Painel 1 — Visão geral Oracle  
2. Painel 2 — Análise operacional de sessões  
3. Painel 3 — BI gerencial de operação Oracle  

## Objetivo
Organizar a apresentação visual dos dados já gerados pelo coletor, incluindo o novo arquivo `fact_oracle_sessions.csv`.

## O que já está pronto
- páginas HTML separadas por finalidade
- nomenclatura em linguagem natural
- filtros visuais
- KPIs
- tabelas e áreas de leitura gerencial

## O que ainda falta ligar
- leitura automática dos CSVs
- regras de filtro reais
- indicadores calculados dinamicamente
- navegação drill-down real entre painéis

## Arquivos
- `index.html`
- `painel_01_visao_geral_oracle.html`
- `painel_02_analise_operacional_sessoes.html`
- `painel_03_bi_gerencial_oracle.html`
- `styles.css`
- `app.js`

## Sugestão prática
Se quiser, o próximo passo ideal é eu converter essa estrutura em:
- HTML com leitura real de CSV local
- Streamlit local
- modelo para Power BI