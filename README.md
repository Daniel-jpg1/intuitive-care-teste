# 🚀 Intuitive Care – Teste Técnico (Processamento de Dados ANS)

Repositório desenvolvido para o **Teste de Entrada para Estagiários v2.0** da Intuitive Care.

O foco desta entrega é a **parte de dados**, cobrindo integralmente os *Testes 1 e 2* do PDF:  
- Integração com os dados públicos da ANS  
- Processamento de arquivos ZIP  
- Normalização  
- Consolidação  
- Validação  
- Enriquecimento  
- Agregação  
- Tratamento de inconsistências  
- Documentação de decisões técnicas (*trade-offs*)  

---

# 🎯 Objetivo Geral

Automatizar o pipeline completo de dados exigido pelo teste:

1. Localizar, baixar e extrair os arquivos de Demonstrações Contábeis dos **últimos 3 trimestres** disponíveis na ANS  
2. Processar arquivos em formatos variados: `.csv`, `.txt`, `.xls`, `.xlsx`  
3. Identificar automaticamente os arquivos contendo **Despesas com Eventos/Sinistros**  
4. Normalizar colunas e padronizar nomes  
5. Consolidar os dados em um único CSV  
6. Validar CNPJ, valores e razão social  
7. Enriquecer o consolidado com o cadastro oficial de operadoras  
8. Agregar despesas por Operadora/UF (total, média, desvio padrão)  
9. Gerar ZIPs finais conforme pedido no PDF  

---

# 🧱 Arquitetura do Projeto

```
src/
 ├── api_ans.py         # Descobre anos/trimestres + baixa os ZIPs
 ├── file_processing.py # Extrai ZIPs + identifica arquivos + normaliza + consolida
 ├── validation.py      # Valida CNPJ, valores e campos obrigatórios
 ├── enrichment.py      # Join com cadastro de operadoras da ANS
 ├── aggregation.py     # Agregação por RazaoSocial + UF
 └── main.py            # Pipeline principal

data/
 ├── raw/               # ZIPs brutos baixados
 ├── processed/         # Arquivos extraídos e normalizados
 └── final/             # Arquivos finais (ZIP + CSV)
```

---

# 🧩 Mapeamento para o PDF do teste

## ✅ **1. Integração com a API pública (ANS)**  
Arquivo: `api_ans.py`

Implementado:

- Scraping simples na estrutura HTML (padrão FTP da ANS)
- Descoberta dinâmica dos anos disponíveis
- Identificação robusta de trimestres com *nomenclaturas variáveis*:
  - `2009_1_trimestre.zip`
  - `1T2024.zip`
  - `2022-2-tri.zip`
  - `3_t_2015.zip`
- Ordenação e seleção dos **últimos 3 trimestres reais**
- Download automático dos arquivos ZIP para `data/raw/`

**Problemas reais resolvidos:**
- Estruturas antigas inconsistentes
- Trimestres com múltiplos arquivos diferentes
- Pastas sem padrão uniforme

---

## ✅ **1.2 Processamento e Normalização**  
Arquivo: `file_processing.py`

Responsável por:

- Extrair todos os ZIPs
- Encontrar apenas arquivos com **Despesas com Eventos/Sinistros**
- Ler arquivos independentemente de:
  - encoding: `utf-8` / `latin1`
  - separador: `;` ou `,`
  - formato: csv / txt / xls / xlsx

### 🔧 Normalização de Colunas  
Foi implementada a função `_normalizar_colunas`, que:

- remove acentos  
- remove aspas  
- remove caracteres estranhos  
- coloca tudo em minúsculo  
- troca espaços por `_`  
- padroniza para `snake_case`  

Isso resolve diferenças como:

- `"Valor Despesas"`  
- `"VALOR_DESPESA "`  
- `"Valor-Despesa"`  

todas virando:

```
valor_despesas
```

---

## 🔎 **Inconsistências encontradas e tratamento (exigido no PDF)**

### **1) CNPJs duplicados com razões sociais diferentes**
- Solução: manter a versão mais recente (cadastro atual)  
- Justificativa: RegistroANS é chave estável → CNPJ pode variar historicamente

### **2) Valores zerados ou negativos**
- Negativos → descartados  
- Zeros → mantidos (podem ser casos reais)

### **3) Trimestres e datas inconsistentes**
- Regex padroniza tudo para formato:
```
ano = YYYY
trimestre = 1 | 2 | 3 | 4
```

### **4) Arquivos antigos sem colunas mínimas**
- Esses arquivos eram irrelevantes para o teste  
- Solução: ignorar de forma controlada + log

### **5) Tipos de coluna variando (int/str)**
- Solução: normalização completa via `astype(str).str.strip()`

---

## ✅ **1.3 Consolidação**
Consolidado inicial contém:

- `registroans`  
- `ano`  
- `trimestre`  
- `valor_despesas`  

Gerado em:

```
data/processed/consolidado_despesas.csv
data/final/consolidado_despesas.zip
```

---

# ✅ **2. Transformação, Validação e Enriquecimento**

## **2.1 Validação** — `validation.py`

Inclui:

- Validação completa de **CNPJ** (formato + dígitos verificadores)
- Filtro de valores inválidos
- Razão Social obrigatória
- Remoção de registros claramente corrompidos

### 🔧 Trade-off: o que fazer com CNPJs inválidos?

Opção adotada:  
**descartar os inválidos** para garantir um dataset limpo.

Justificativa:

- facilidade de análise  
- reduz ruído  
- mantém coerência estatística  

---

## **2.2 Enriquecimento (join com cadastro)** — `enrichment.py`

Fonte:  
`https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/`

Após normalização, junta com o consolidado trazendo:

- `cnpj`
- `razao_social`
- `registroans`
- `modalidade`
- `uf`

### Problemas tratados:

- CNPJs repetidos no cadastro → seleciona registro mais recente  
- Operadoras sem match → marcadas e/ou removidas conforme regra  
- Tipos diferentes (`int vs str`) → normalização pré-merge

---

# ✅ **2.3 Agregação Estatística** — `aggregation.py`

Agrupa por:

```
razao_social, uf
```

E calcula:

- **total** de despesas  
- **média** trimestral  
- **desvio padrão** (detecta variações altas)

Ordenado do maior para o menor.

Gera:

```
data/final/despesas_agregadas.csv
data/final/Teste_{meu_nome}.zip
```

---

# 🔧 Trade-offs técnicos (exigidos pelo PDF)

### **1) Processar tudo em memória vs incremental**
Escolha: **em memória**

Prós:
- código mais simples
- pandas é rápido para o volume esperado
- depuração fácil

Contras:
- mais uso de RAM (mas irrelevante para os tamanhos atuais)

---

### **2) Chave de join: CNPJ vs RegistroANS**
Escolha: **RegistroANS como chave primária**

Prós:
- estabilidade maior ao longo dos anos
- evita problemas de substituição de CNPJ
- operação consistente com demos contábeis

---

### **3) CNPJs inválidos**
Escolha: **descartar**

Prós:
- dataset limpo e estável  
- reduz anomalias artificiais  
- evita erros acumulados nas agregações

---

### **4) Ordenação e agregação**
Escolha: **ordenar em memória com pandas**

Prós:
- performance excelente para poucos milhares de registros  
- simplicidade  
- código direto e auditável  

---

# ✔ Conclusão

O pipeline cobre integralmente os requisitos dos **Testes 1 e 2 do PDF**, com justificativas de escolhas técnicas e tratamento explícito de inconsistências.

O código foi organizado em módulos independentes para garantir clareza, manutenibilidade e facilidade de avaliação.
