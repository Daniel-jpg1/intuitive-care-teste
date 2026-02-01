🚀 Intuitive Care – Teste Técnico (WIP)

Repositório dedicado ao teste técnico da Intuitive Care, desenvolvido em Python.
Atualmente em construção e evoluindo por módulos.

📦 Módulo 1 — Integração com API de Dados Abertos da ANS

✔️ Status do Progresso

| Etapa                                            | Status |
| ------------------------------------------------ | ------ |
| Listar anos disponíveis                          | ✅      |
| Identificar e coletar arquivos ZIP por trimestre | ✅      |
| Baixar os últimos 3 trimestres disponíveis       | ✅      |
| Extrair arquivos                                 | ✅      |
| Normalizar dados                                 | ✅      |
| Consolidação e enriquecimento                    | ⏳      |
| API + Frontend                                   | ⏳      |

🧠 Decisões Técnicas (fase atual)

As decisões abaixo refletem somente o módulo 1 e o início do processamento de arquivos, concluídos até agora:

🔹 Linguagem escolhida

Python, pela rapidez no desenvolvimento e pela facilidade para lidar com dados (pandas, requests, BS4).

🔹 Arquitetura inicial

Código organizado em módulos dentro de src/, começando por:

src/  
 ├── api_ans.py         # Acesso, listagem e download de arquivos da ANS  
 └── file_processing.py # Extração, leitura e normalização dos arquivos de demonstrações contábeis

🔹 Bibliotecas utilizadas

• requests → para fazer requisições HTTP  
• BeautifulSoup → para parsear o HTML da estrutura da ANS  
• pathlib → para manipulação limpa de caminhos  
• re (regex) → para identificar arquivos por trimestre  
• pandas → para leitura e manipulação de dados tabulares  

🔹 Estratégia de busca

• Scraping simples na pasta principal da ANS (padrão FTP em HTML).  
• Identificação automática dos anos disponíveis.  
• Seleção dos 3 trimestres mais recentes, independente do formato dos arquivos (ex: 1T2025.zip, 2025_1_trimestre.zip, 2-tri.zip).  

🔹 Funções auxiliares

Criação da função _get_soup() para:

• Reutilizar o código de requisição + parse  
• Centralizar erros  
• Deixar outros métodos mais limpos  

📦 Módulo 2 — Processamento interno dos arquivos (iniciado)

Arquivo principal: src/file_processing.py

Funcionalidades já implementadas:

• Extração dos arquivos .zip baixados para a pasta data/processed/  
• Identificação inicial dos arquivos relevantes (CSV/TXT/XLS/XLSX)  
• Leitura robusta dos arquivos, testando automaticamente combinações de encoding (utf-8 / latin1) e separador (; / ,)  
• Normalização dos nomes de colunas (minúsculo, sem acentos, com padrão único)  
• Extração de Ano e Trimestre a partir do nome dos arquivos  
• Geração de um consolidado inicial com as colunas:
  - RegistroANS  
  - Ano  
  - Trimestre  
  - ValorDespesas  

• Criação automática dos arquivos:
  - consolidado_despesas.csv  
  - consolidado_despesas.zip  

📥 Progresso Atual

O pipeline já é capaz de:

✔ Buscar a pasta correta na ANS  
✔ Listar os anos existentes  
✔ Identificar zips por trimestre mesmo com nomes diferentes  
✔ Ordenar e selecionar os últimos 3  
✔ Fazer download automático dos arquivos ZIP  
✔ Extrair e ler os arquivos de demonstrações contábeis em vários formatos  
✔ Normalizar colunas e gerar um consolidado inicial de despesas por RegistroANS/Ano/Trimestre  

🛠 Próximos Passos

• Enriquecer o consolidado com o cadastro de operadoras (CNPJ, Razão Social, UF, Modalidade)  
• Implementar validações de dados (CNPJ, valores positivos, razão social não vazia)  
• Agregar despesas por Razão Social e UF  
• Integrar tudo no main.py e seguir para a parte de SQL, API e Frontend  

📄 Observações

Este repositório está sendo montado progressivamente.
Os commits refletem a evolução do raciocínio e construção da solução.
