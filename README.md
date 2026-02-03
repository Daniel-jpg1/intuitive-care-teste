# 🚀 Intuitive Care – Teste Técnico (Processamento de Dados ANS)

Repositório desenvolvido para o **Teste de Entrada para Estagiários v2.0** da Intuitive Care.

Este projeto implementa **todas as 4 etapas** do PDF, incluindo:
- Coleta de dados públicos da ANS  
- Processamento e normalização de arquivos  
- Consolidação, validação e enriquecimento  
- Agregação estatística  
- Banco de dados + queries SQL  
- API em FastAPI  
- Frontend em Vue.js  
- Documentação de *todos* os trade-offs técnicos solicitados  

---

# 🎯 Objetivo Geral

Automatizar o pipeline completo de dados da ANS:

1. Localizar os **últimos 3 trimestres** disponíveis no repositório oficial  
2. Fazer download e extração dos ZIPs  
3. Encontrar automaticamente arquivos de **Despesas com Eventos/Sinistros**  
4. Normalizar colunas e padronizar formatos  
5. Consolidar valores trimestrais  
6. Validar dados (CNPJ, valores, razão social)  
7. Enriquecer com o cadastro oficial de operadoras  
8. Agregar despesas (total, média, desvio padrão)  
9. Gerar o ZIP final solicitado pelo PDF  
10. Criar API + dashboard em Vue  

---

# 🧱 Arquitetura do Projeto

```
src/
 ├── api_ans.py          # Identifica trimestres, baixa ZIPs
 ├── file_processing.py  # Extrai arquivos, normaliza, consolida
 ├── validation.py       # Validação de CNPJ e dados obrigatórios
 ├── enrichment.py       # Join com cadastro de operadoras
 ├── aggregation.py      # Agregações estatísticas
 ├── api_app.py          # API FastAPI (Etapa 4)
 └── main.py             # Pipeline principal (executa tudo)

frontend/
 └── Vue.js dashboard

sql/
 ├── schema.sql          # Criação das tabelas
 ├── import.sql          # Exemplos de LOAD DATA
 └── queries.sql         # Queries analíticas (Etapa 3)

data/
 ├── raw/                # ZIPs brutos baixados
 ├── processed/          # Arquivos normalizados
 └── final/              # Consolidados finais + ZIP de entrega
```

---

# 🧩 Mapeamento para o PDF

### ✔ Etapa 1 — Extração dos dados
- Descoberta dos anos e trimestres disponíveis  
- Scraping leve da estrutura HTML (padrão FTP)  
- Tratamento de nomes diferentes:
  - `1T2024.zip`
  - `2009_3_trimestre.zip`
  - `2022-2-tri.zip`
- Seleção correta dos **3 trimestres mais recentes**

---

### ✔ Etapa 2 — Processamento, normalização e enriquecimento
Inclui:
- Leitura tolerantente (encoding, separador, formatos variados)
- Normalização de colunas (snake_case, sem acentos)
- Consolidação trimestral
- Validação completa do CNPJ
- Join com cadastro oficial da ANS
- Agregação por Razão Social + UF

---

### ✔ Etapa 3 — Banco de dados + queries analíticas
Inclui:
- Tabelas `operadoras`, `despesas_consolidadas`, `despesas_agregadas`
- `AUTO_INCREMENT`, índices, DECIMAL para valores monetários
- Queries exigidas:
  - Top 5 crescimento percentual
  - Despesas por UF (+ média por operadora)
  - Operadoras acima da média geral
- Tratamento de operadoras sem todos os trimestres

---

### ✔ Etapa 4 — API + Dashboard
- API com FastAPI  
- Paginação offset-based  
- Busca por **CNPJ ou Razão Social**  
- Endpoints:
  - `/api/operadoras`
  - `/api/operadoras/{cnpj}`
  - `/api/operadoras/{cnpj}/despesas`
  - `/api/estatisticas`
- Dashboard em Vue.js consultando a API

## ▶ Como rodar o projeto (pipeline + API + frontend)

---

# 🔧 Como rodar o projeto (backend + frontend)

# 1) Clonar o repositório
git clone https://github.com/Daniel-jpg1/intuitive-care-teste.git
cd intuitive-care-teste

# 2) Criar e ativar o ambiente virtual (Python)
# Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# (Opcional para Windows PowerShell)
# py -m venv venv
# .\venv\Scripts\Activate.ps1

# 3) Instalar as dependências Python
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 4) Executar o pipeline de dados
# (Baixa os últimos 3 trimestres na ANS, processa tudo e gera os CSV/ZIP em data/)
python src/main.py

# 5) Subir a API (FastAPI)
uvicorn src.api_app:app --reload
# A API estará disponível em:
#   http://127.0.0.1:8000/docs

# 6) Subir o frontend (Vue + Vite) em OUTRO terminal
# (rodar estes comandos dentro da pasta intuitive-care-teste)
cd frontend
npm install
npm run dev
# O frontend estará disponível em:
#   http://localhost:5173/

---

### 7) Resumo rápido
1. `python src/main.py` → executa toda a pipeline de dados  
2. `uvicorn src.api_app:app --reload` → sobe a API  
3. `cd frontend && npm run dev` → inicia o dashboard Vue  
4. Abrir `http://localhost:5173` no navegador  


# 📦 Arquivos gerados pelo pipeline

```
data/final/
 ├── consolidado_despesas.csv
 ├── despesas_agregadas.csv
 ├── Teste_Carlos_Daniel.zip  ← arquivo final de entrega
```

---

# 🧠 **Trade-offs Técnicos**

---

## **1. Processamento: em memória vs incremental**
**Escolha:** em memória (Pandas)  
**Motivo:** performance excelente para poucos milhares de linhas, código mais simples.

---

## **2. Inconsistência: CNPJs duplicados no consolidado**
**Escolha:** usar RegistroANS como chave e descartar duplicados antigos.  
**Motivo:** RegistroANS é estável, CNPJ muda historicamente.

---

## **3. Inconsistência: valores zerados/negativos**
- Negativos → descartados  
- Zeros → mantidos  

Justificativa: zeros são válidos; negativos são erros.

---

## **4. Inconsistência: trimestres com formato inconsistente**
**Escolha:** padronizar com regex.  
**Motivo:** múltiplos formatos na ANS.

---

## **5. CNPJs inválidos**
**Escolha:** descartar.  
**Motivo:** evita poluir estatísticas e análises.

---

## **6. Estratégia de join: CNPJ vs RegistroANS**
**Escolha:** RegistroANS  
**Motivo:** mais estável, usado pela própria ANS.

---

## **7. Registros sem match no cadastro**
**Escolha:** descartar + log.  
**Motivo:** operadora sem cadastro ativo não compõe estatísticas.

---

## **8. Cadastro com CNPJs repetidos**
**Escolha:** ficar com o mais recente.  
**Motivo:** duplicatas são comuns no dataset da ANS.

---

## **9. Ordenação: Pandas vs SQL**
**Escolha:** Pandas  
**Motivo:** evita dependência adicional e volume é pequeno.

---

## **10. Normalização: tabela única vs tabelas separadas**
**Escolha:** tabela única (desnormalizada)  
**Motivo:** baixa frequência de atualização, queries simples.

---

## **11. Tipos de dados: DECIMAL vs FLOAT**
**DECIMAL(18,2)**  
**Motivo:** precisão monetária. FLOAT introduz erro.

---

## **12. Importação: NULLs, strings e datas ruins**
**Escolha:** coercão + descarte seguro.  
**Motivo:** evita registros corrompidos.

---

## **13. Query 1 — operadoras sem todos os trimestres**
**Escolha:** considerar apenas operadoras com pelo menos 2 pontos.  
**Motivo:** não existe “crescimento” com um único trimestre.

---

## **14. Query 3 — abordagem escolhida**
**Escolha:** subquery + flag acima da média.  
**Motivo:** simples, performático, legível.

---

## **15. Framework backend: Flask vs FastAPI**
**Escolha:** FastAPI  
**Motivo:** melhor validação, melhor documentação automática.

---

## **16. Paginação: offset vs cursor vs keyset**
**Escolha:** offset-based  
**Motivo:** volume pequeno, implementação simples.

---

## **17. Estatísticas: cálculo vs cache**
**Escolha:** calcular sempre  
**Motivo:** dados pequenos, atualização eventual.

---

## **18. Estrutura da resposta: lista vs lista + metadados**
**Escolha:** lista + metadados  
**Motivo:** melhor UX no frontend.

---

## **19. Busca: servidor vs cliente vs híbrido**
**Escolha:** servidor  
**Motivo:** reduz carga no frontend e funciona melhor para paginação.

---

## **20. Estado do frontend: props vs Pinia**
**Escolha:** props  
**Motivo:** app pequeno, sem necessidade de store global.

---

## **21. Performance na tabela**
**Escolha:** paginação server-side  
**Motivo:** evita renderizar centenas de linhas.

---

## **22. Tratamento de erros/loading**
**Escolha:** mensagens simples e claras  
**Motivo:** UX direta e objetiva para teste técnico.

---
