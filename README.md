# Intuitive Care – Teste Técnico (WIP)

Primeiro módulo: integração com a API de dados abertos da ANS.

Status:
- [x] Listar anos disponíveis
- [x] Identificar e coletar arquivos ZIP por trimestre
- [x] Baixar os últimos 3 trimestres disponíveis
- [ ] Extrair arquivos
- [ ] Normalizar dados
- [ ] Consolidação e enriquecimento
- [ ] API + Frontend

Este repositório ainda está em desenvolvimento.

📌 Decisões Técnicas (fase atual – módulo 1)

Projeto iniciado com Python por ser mais rápido para manipulação de dados.

Organização do código feita em módulos (src/api_ans.py como primeiro módulo).

Uso do requests + BeautifulSoup para parse de HTML na ANS.

Uso de função auxiliar _get_soup() para tornar o código mais limpo e reutilizável.

Primeira etapa finalizada: download dos últimos 3 trimestres.

Documentações mais completas e trade-offs serão adicionados ao longo dos próximos módulos.