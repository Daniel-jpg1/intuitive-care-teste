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
| Extrair arquivos                                 | ⏳      |
| Normalizar dados                                 | ⏳      |
| Consolidação e enriquecimento                    | ⏳      |
| API + Frontend                                   | ⏳      |

🧠 Decisões Técnicas (fase atual)

As decisões abaixo refletem somente o módulo 1, concluído até agora:

🔹 Linguagem escolhida

Python, pela rapidez no desenvolvimento e pela facilidade para lidar com dados (pandas, requests, BS4).

🔹 Arquitetura inicial

Código organizado em módulos dentro de src/, começando por:

src/
 └── api_ans.py   # Acesso, listagem e download de arquivos da ANS

🔹 Bibliotecas utilizadas

• requests → para fazer requisições HTTP

• BeautifulSoup → para parsear o HTML da estrutura da ANS

• pathlib → para manipulação limpa de caminhos

• re (regex) → para identificar arquivos por trimestre

🔹 Estratégia de busca

• Scraping simples na pasta principal da ANS (padrão FTP em HTML).

• Identificação automática dos anos disponíveis.

• Seleção dos 3 trimestres mais recentes, independente do formato dos arquivos (ex: 1T2025.zip, 2025_1_trimestre.zip, 2-tri.zip).

🔹 Funções auxiliares

Criação da função _get_soup() para:

• Reutilizar o código de requisição + parse

• Centralizar erros

• Deixar outros métodos mais limpos

📥 Progresso Atual

O pipeline já é capaz de:

✔ Buscar a pasta correta na ANS
✔ Listar os anos existentes
✔ Identificar zips por trimestre mesmo com nomes diferentes
✔ Ordenar e selecionar os últimos 3
✔ Fazer download automático dos arquivos ZIP

As próximas etapas incluem:

• Processamento interno dos arquivos

• Normalização

• Consolidação

• Enriquecimento com base cadastral

• API + Frontend

🛠 Próximos Passos

• Implementar extração dos arquivos .zip

• Criar normalização genérica de colunas

• Iniciar documentação de trade-offs

• Consolidar e enriquecer dados (módulo 2)

📄 Observações

Este repositório está sendo montado progressivamente.
Os commits refletem a evolução do raciocínio e construção da solução.