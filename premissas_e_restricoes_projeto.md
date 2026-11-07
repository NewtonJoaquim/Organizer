# Premissas e Restrições do Projeto (Escopo do Projeto)
**Projeto Aplicado:** Organizer App — Organizador Inteligente de Dados e Planilhas  
**Instituição:** XP Educação (XPE) — Pós-Graduação em Inteligência Artificial e Engenharia de Software  
**Data:** 01 de Novembro de 2026  
**Status:** Documento de Planejamento de Escopo (Seção 1.2.2 do Relatório)

---

## 1. Visão Geral e Fundamentação Conceitual

No gerenciamento de projetos ágeis e na engenharia de software corporativa, a delimitação de **Premissas e Restrições** constitui o alicerce para a definição precisa do **Escopo do Projeto**. Esses dois fatores estabelecem as condições operacionais e as fronteiras sob as quais o **Organizer App** será planejado, desenvolvido, testado e validado ao longo das 3 Sprints de experimentação.

De acordo com as melhores práticas metodológicas (PMBOK e Scrum):
* **Premissas:** São sentenças ou condições assumidas como verdadeiras no momento do planejamento, porém não passíveis de comprovação absoluta a priori, pois dependem de variáveis e fatores externos fora do controle direto da equipe de desenvolvimento. Exigem monitoramento contínuo, pois, caso se mostrem falsas, podem desestabilizar o cronograma, a arquitetura ou a viabilidade do produto.
* **Restrições:** São limitações, fronteiras e restrições inegociáveis, internas ou externas ao projeto, que determinam como e quando o trabalho pode ser executado. Englobam restrições temporais (prazos fixos), financeiras/orçamentárias, tecnológicas, legais/regulatórias e limitações de capacidade da equipe de desenvolvimento.

---

## 2. Premissas do Projeto e Análise de Consequências/Impactos

A Tabela 2.1 detalha as premissas fundamentais estabelecidas para a execução do **Organizer App**, acompanhadas das perguntas diagnósticas: *Quais são as premissas para a execução?* e *Quais as consequências (impactos) e planos de mitigação caso essas premissas não sejam verdadeiras?*

### Tabela 2.1: Matriz de Premissas, Impactos e Ações de Mitigação

| ID | Premissa Estabelecida | Fator Externo Dependente | Consequência / Impacto caso Falsa | Ação Preventiva / Mitigação Planejada |
| :---: | :--- | :--- | :--- | :--- |
| **PR-01** | **Disponibilidade e Estabilidade das APIs de LLM:** Assume-se que os provedores de modelos de linguagem (OpenAI/Google Gemini) manterão alta disponibilidade (> 99,5%), latência de resposta baixa (< 3s) e suporte nativo a saídas estruturadas (*Structured Outputs* via JSON Schema). | Provedor de Nuvem e infraestrutura da API de IA externa. | Falha ou lentidão severa na extração de intenções e no mapeamento semântico de cabeçalhos, estourando o SLA de 15 segundos do projeto. | Implementação de arquitetura de fallback com *timeout* curto, tentativas com retrocesso exponencial (*backoff*) e suporte secundário a provedores alternativos de API. |
| **PR-02** | **Natureza Tabular e Integridade Básica dos Arquivos:** Assume-se que as planilhas enviadas pelos clientes/parceiros estão em formatos legíveis de planilhas (`.xlsx` ou `.xls`), contendo tabelas de dados estruturáveis por linhas e colunas (e não imagens escaneadas, PDFs ou arquivos corrompidos). | Hábitos de geração e exportação de dados de parceiros e sistemas legados (ERPs). | Incompatibilidade imediata com as bibliotecas de processamento tabular (Pandas/openpyxl), gerando erro de ingestão na primeira camada. | Criação de módulo de validação de integridade do arquivo na entrada com mensagens de erro amigáveis orientando o usuário a reenviar o arquivo em formato de pasta de trabalho válido. |
| **PR-03** | **Aceitação Corporativa do Tráfego de Metadados (LGPD):** Assume-se que as empresas e operadores de áreas de negócios aceitam enviar **apenas os nomes das colunas e instruções** para a nuvem da IA, confiando que o processamento dos dados numéricos sensíveis permanece local com descarte imediato. | Departamentos de compliance, jurídico e segurança da informação das empresas clientes. | Rejeição comercial de uso por políticas corporativas restritivas que vetem qualquer interação externa com nuvem de IA pública. | Política transparente de *Zero Data Retention*, auditoria de tráfego demonstrando que valores numéricos nunca deixam o ambiente local e desenho conceitual para suportar modelos locais (SLMs) no futuro. |
| **PR-04** | **Capacidade de Formulação em Linguagem Natural:** Assume-se que os profissionais de áreas de negócios (Citizen Data Scientists) conseguem expressar suas intenções de organização em português corrente de forma minimamente coerente (ex.: *"ordene por data e depois valor"*). | Clareza de comunicação e repertório básico do usuário final. | Ambiguidade excessiva no comando em linguagem natural, levando o modelo de IA a gerar ordenações indesejadas pelo operador. | Fornecimento de botões de atalho com *templates* de comandos frequentes (ex.: *"Ordenar por data mais recente"*, *"Padronizar colunas"*), além de campo de texto livre e tela de confirmação prévia. |
| **PR-05** | **Manutenção do Baixo Custo Unitário de Inferência:** Assume-se que os preços por token de modelos leves e eficientes de IA permanecerão acessíveis (< US$ 0,15 por 1M de tokens de entrada), mantendo o custo por planilha abaixo de R$ 0,01. | Política comercial e de preços dos provedores globais de IA. | Aumento drástico do custo de operação do produto, inviabilizando a margem bruta projetada de 90% para o modelo de negócios SaaS. | Otimização contínua do tamanho dos *prompts* de sistema e minimização estrita da carga de metadados trafegada, limitando o consumo a menos de 800 tokens por requisição. |
| **PR-06** | **Compatibilidade do Ecossistema Microsoft Office Add-in:** Assume-se que a plataforma *Office JavaScript API* permite criar painéis laterais de suplementos estáveis no Excel Web e Desktop sem bloqueio por políticas restritivas de TI corporativa. | Diretrizes de segurança de TI corporativa (GPOs) e ecossistema de extensões da Microsoft. | Impossibilidade de o usuário corporativo instalar o suplemento lateral no Excel de sua máquina corporativa sem aprovação de TI. | Manutenção da aplicação web responsiva como canal autônomo primário de contingência, permitindo o uso completo do sistema via navegador sem depender de privilégios de instalação de suplementos. |

---

## 3. Restrições do Projeto

As restrições representam os limites e fronteiras rígidas que delimitam o que a equipe do projeto pode e não pode fazer, condicionando a tomada de decisões técnicas e gerenciais.

### 3.1. Restrições Temporais (Cronograma Acadêmico)
* **Prazo Fixo de Entrega:** O projeto deve ser planejado, implementado, testado e documentado rigorosamente dentro do prazo limite do ciclo acadêmico do Projeto Aplicado.
* **Alocação por Sprints:** O desenvolvimento deve ser estruturado e finalizado no horizonte fechado de **21 dias corridos**, distribuídos em **3 Sprints ágeis semanais de 7 dias cada**.
* **Entregas Modulares Obrigatórias:** A Sprint 1 deve focar no núcleo de processamento e segurança; a Sprint 2 na consolidação de abas e validação humana; e a Sprint 3 na prototipação de canal (Add-in) e validação experimental com as personas.

### 3.2. Restrições Orçamentárias e Financeiras
* **Orçamento Direto Nulo (Zero Budget para Infraestrutura Dedicada):** O projeto não conta com verba para aluguel de servidores dedicados corporativos, contratação de servidores de GPUs ou contratação de serviços corporativos pagos de engenharia de dados.
* **Operação com Recursos Gratuitos ou de Baixo Custo:** Todas as dependências externas devem se apoiar em planos de nível gratuito (*free tier*) de plataformas de hospedagem em nuvem (ex.: Render, Vercel ou instâncias locais) e consumo de créditos controlados de APIs de IA para os testes práticos de validação.

### 3.3. Restrições Técnicas, Arquiteturais e de Escopo
* **Limite Volumétrico de Processamento no MVP:** O sistema é desenhado para operar de forma síncrona com pastas de trabalho de até **10.000 linhas** e tamanho máximo de arquivo de **20 MB**, garantindo o cumprimento do SLA de resposta em menos de 15 segundos sem incorrer em timeouts de requisições HTTP.
* **Agnosticismo a Hardware Dedicado:** Toda a rotina determinística de leitura, manipulação e ordenação matemática deve rodar em computadores comuns de desenvolvimento com consumo moderado de memória RAM (< 2 GB por requisição).
* **Restrição de Formato de Entrada e Saída:** O suporte no MVP é estritamente delimitado a planilhas no formato Microsoft Excel OpenXML (`.xlsx`) e planilhas legadas (`.xls`), ficando fora do escopo a leitura de bancos de dados relacionais diretos, APIs proprietárias ou documentos PDF.
* **Navegadores Homologados:** A interface web será otimizada para navegadores modernos com suporte a padrões web modernos (Google Chrome, Microsoft Edge, Mozilla Firefox e Safari), sem suporte a navegadores legados descontinuados (Internet Explorer).

### 3.4. Restrições Regulatórias e Legais (Governança e LGPD)
* **Conformidade com a LGPD (Lei nº 13.709/2018):** O projeto possui restrição mandatória quanto à não retenção persistente de dados pessoais ou comerciais sensíveis. Nenhum dado contido nas linhas das planilhas processadas pode ser armazenado em bancos de dados relacionais da aplicação ou utilizado para treinamento de modelos de terceiros (*Zero Data Retention*).
* **Descarte Imediato:** Todos os arquivos temporários gerados em disco durante a operação devem ser expurgados imediatamente após a conclusão do download ou após expiração de sessão temporal.

### 3.5. Restrições de Equipe e Recursos Humanos
* **Equipe Unipessoal (Desenvolvedor Único):** O projeto é conduzido por um único estudante de pós-graduação, que acumula as funções de Product Owner, Arquiteto de Software, Engenheiro de Dados e Designer de UX/UI.
* **Capacidade de Trabalho:** Dedicação estimada entre 15 e 20 horas semanais de desenvolvimento e experimentação, exigindo priorização rígida do backlog e evitando funcionalidades supérfluas que dilatem o esforço.

---

## 4. Listagem e Categorização de Recursos Necessários

Conforme exigido pelo referencial metodológico da XP Educação, a Tabela 2.2 cataloga todos os recursos necessários para a realização eficiente do Projeto Aplicado:

### Tabela 2.2: Matriz de Recursos do Projeto

| Categoria do Recurso | Recurso Específico | Finalidade e Aplicação no Projeto | Disponibilidade / Acesso |
| :--- | :--- | :--- | :--- |
| **Recursos Humanos** | **Pesquisador e Engenheiro de Software (Autor do Projeto)** | Execução integral do ciclo de vida: levantamento de hipóteses, arquitetura, codificação backend/frontend, condução de testes e redação acadêmica. | Dedicação semanal contínua ao longo das 3 Sprints. |
| **Recursos Humanos** | **Orientador Acadêmico (XP Educação)** | Validação metodológica, feedback sobre artefatos e direcionamento pedagógico do relatório final. | Sessões de tutoria e revisões periódicas da plataforma de ensino. |
| **Recursos Humanos** | **Operadores de Teste (Personas Carlos, Mariana, Rodrigo)** | Participação em entrevistas de validação e submissão de planilhas desorganizadas de teste para avaliação de usabilidade e ganho de tempo. | Contato direto via entrevistas qualitativas (*The Mom Test*). |
| **Recursos de Software / Backend** | **Linguagem Python (v3.11+)** | Linguagem principal para desenvolvimento das rotinas de orquestração de IA, heurísticas de leitura e processamento tabular determinístico. | Software livre, código aberto e multiplataforma. |
| **Recursos de Software / Backend** | **Bibliotecas Pandas e openpyxl** | Manipulação em memória, leitura de arquivos binários `.xlsx`, detecção de densidade de cabeçalhos e ordenação matemática estável (*mergesort*). | Bibliotecas livres de código aberto via gerenciador `pip`. |
| **Recursos de Software / Backend** | **Framework Flask / FastAPI** | Construção da API RESTful de backend responsável pelos endpoints de ingestão multipart, processamento e entrega binária. | Frameworks open-source padrão de mercado. |
| **Recursos de Software / IA** | **API de Modelos de Linguagem (OpenAI / Gemini)** | Tradução semântica de intenções expressas em português e resolução de sinonímias entre cabeçalhos via *Structured Outputs* (Pydantic). | Acesso via chave de API gerenciada por variáveis de ambiente. |
| **Recursos de Software / Frontend** | **React, Vite e Tailwind CSS** | Construção da interface gráfica web de autosserviço: responsiva, limpa e com feedback visual de upload e download. | Ecossistema web livre e de alta produtividade. |
| **Recursos de Infraestrutura e IDE** | **Ambiente de Desenvolvimento (VS Code)** | Ambiente integrado de desenvolvimento de código com terminal integrado e suporte a extensões Python e React. | Software livre mantido pela comunidade. |
| **Recursos de Gestão e Documentação** | **Git e Repositório GitHub** | Controle de versionamento de código, rastreabilidade de alterações e guarda segura do repositório acadêmico. | Repositório em nuvem com acesso seguro por chaves SSH. |
| **Recursos de Gestão e Documentação** | **Trello / Planner / Excel** | Acompanhamento do cronograma ágil das Sprints, gestão de tarefas e controle do Backlog do Produto. | Ferramentas gratuitas de gestão visual Kanban. |
| **Recursos de Hardware** | **Computador Pessoal (Notebook/Desktop)** | Máquina hospedeira do ambiente local de desenvolvimento com sistema operacional Windows 11, processador multi-core e 16 GB de memória RAM. | Recurso próprio disponível do estudante. |
| **Recursos de Conectividade** | **Conexão de Banda Larga à Internet** | Acesso às APIs de IA em nuvem, download de bibliotecas, comunicação com orientadores e pesquisa acadêmica. | Infraestrutura residencial contínua. |

---

## 5. Listagem de Habilidades e Conhecimentos Necessários

Para garantir que o escopo seja executado com qualidade e que as metas de aceitação sejam atingidas, mapearam-se as competências intelectuais, técnicas e metodológicas essenciais para o desenvolvimento da solução:

### 5.1. Habilidades Técnicas (Hard Skills)
1. **Engenharia de Software e Desenvolvimento Backend:**
   * Proficiência na linguagem de programação Python e arquitetura de aplicações web baseadas em APIs RESTful.
   * Domínio de manipulação de fluxos de entrada e saída (*streams* de arquivos multipart/form-data) e arquiteturas assíncronas leves.
2. **Manipulação e Engenharia de Dados Tabulares:**
   * Conhecimento aprofundado da biblioteca Pandas para filtragem, normalização de strings (*snake_case*, remoção de caracteres especiais), fatiamento (*slicing*) de dataframes e algoritmos determinísticos de ordenação multi-coluna.
   * Conhecimento da biblioteca openpyxl para leitura estruturada de metadados, formatação de células e inspeção de linhas ocultas ou mescladas.
3. **Inteligência Artificial Aplicada e Engenharia Semântica:**
   * Domínio de integração de APIs de Large Language Models (LLMs) corporativos.
   * Prática de modelagem de esquemas estruturados via Pydantic (*Structured Outputs / JSON Schema*), assegurando previsibilidade nas respostas do modelo sem ocorrência de alucinações de formato.
   * Construção de *prompts* enxutos voltados para a orquestração semântica de schema e extração de critérios de ordenação a partir de comandos coloquiais.
4. **Desenvolvimento Frontend e Experiência do Usuário (UX/UI):**
   * Habilidade no ecossistema JavaScript moderno (React, TypeScript e gerenciamento de estado local).
   * Criação de layouts responsivos com Tailwind CSS, focados em clareza, acessibilidade e redução da curva de aprendizado para profissionais não técnicos.
5. **Segurança da Informação e Compliance:**
   * Boas práticas de segurança de aplicações web: higienização de nomes de arquivos para prevenção de ataques de injeção de caminho (*Path Traversal*).
   * Diretrizes de conformidade com a LGPD: implementação prática de políticas de retenção zero (*Zero Data Retention*) e gestão segura de segredos via variáveis de ambiente (`.env`).

### 5.2. Habilidades Metodológicas e de Gestão de Negócios
1. **Design Thinking e Engenharia de Problemas:**
   * Capacidade de conduzir as etapas de Imersão Preliminar, Imersão Profunda, Síntese e Ideação.
   * Aplicação prática dos frameworks POEMS, Matriz CSD e entrevistas investigativas baseadas na metodologia *The Mom Test* para validar dores reais sem vieses.
2. **Gestão Ágil de Projetos (Scrum / Kanban):**
   * Estruturação de Backlog de Produto priorizado com base na Matriz GUT de incertezas e riscos.
   * Planejamento, execução, revisão e retrospectiva de 3 Sprints ágeis com critérios de aceitação objetivos.
3. **Modelagem de Negócios e Proposta de Valor:**
   * Elaboração do Canvas de Proposta de Valor e Canvas do Projeto Aplicado.
   * Quantificação de retorno financeiro corporativo (Hard ROI, cálculo de homem-hora economizado e viabilidade SaaS).

### 5.3. Habilidades Comportamentais (Soft Skills)
1. **Comunicação Técnica e Redação Acadêmica:** Habilidade de traduzir desafios computacionais complexos em linguagem formal, clara e acessível, alinhada com os padrões exigidos no relatório do curso da XP Educação.
2. **Pensamento Crítico e Rigor Lógico:** Capacidade de separar onde a inteligência artificial é necessária (tradução semântica) e onde rotinas matemáticas tradicionais são mandatórias (preservação numérica estrita de 100%).
3. **Autonomia e Gestão do Tempo:** Disciplina para manter o ritmo sequencial de entregas entre as Sprints sob restrição estrita de prazo.

---

## 6. Síntese Comparativa: Premissas vs. Restrições

Para consolidação visual e rápida consulta durante o preenchimento da seção **1.2.2** do relatório oficial, a Tabela 2.3 sintetiza a correlação entre as premissas e as restrições que regem o projeto:

### Tabela 2.3: Síntese de Condições de Escopo do Organizer App

| Dimensão de Escopo | Premissas (Sentenças Assumidas como Verdadeiras) | Restrições (Limitações e Fronteiras Inegociáveis) |
| :--- | :--- | :--- |
| **Tecnologia & IA** | • APIs de IA externas manterão alta disponibilidade e suporte a saídas estruturadas.<br>• Modelos de linguagem conseguem interpretar linguagem natural em português com precisão. | • Sem orçamento para servidores dedicados ou GPUs locais.<br>• Obrigatório uso exclusivo de metadados para mitigar custos de API. |
| **Dados & Formato** | • Arquivos de entrada são pastas de trabalho tabulares (`.xlsx`/`.xls`) geradas por ERPs ou usuários.<br>• Colunas contêm dados compatíveis para normalização de cabeçalhos. | • Volume máximo por arquivo limitado a 10.000 linhas e 20 MB no MVP.<br>• Suporte inicial restrito a formatos Excel (sem suporte a PDFs/OCR). |
| **Prazo & Entrega** | • Três sprints de desenvolvimento são suficientes para testar o MVP da solução.<br>• As métricas de acurácia serão atingíveis no ciclo acadêmico. | • Conclusão mandatória no ciclo de 21 dias (3 sprints semanais de 7 dias).<br>• Equipe unipessoal com limite semanal de 15 a 20 horas de dedicação. |
| **Segurança & Legal** | • Parceiros corporativos aceitam a ingestão de metadados se houver garantia de retenção zero.<br>• A arquitetura atende às exigências de privacidade das PMEs. | • Conformidade mandatória com a LGPD (Lei 13.709/2018).<br>• Proibição de armazenamento persistente de dados sensíveis em banco de dados. |
| **Canais & Mercado** | • A ferramenta será utilizada por profissionais sem conhecimento em código (*Citizen Data Scientists*).<br>• Suplementos Office JS são viáveis em estações Windows/Web. | • Canal primário garantido via aplicação web autônoma caso haja restrição de instalação de add-in pela TI das empresas parceiras. |

---

## 7. Conclusão da Análise de Escopo

O mapeamento detalhado das premissas e restrições garante que o **Organizer App** possua um escopo exequível, pragmático e robusto. Ao reconhecer antecipadamente as dependências externas (como a estabilidade das APIs de LLM e o formato dos arquivos) e estabelecer planos de contingência, aliados a restrições rígidas de tempo (3 Sprints), custo (zero infraestrutura dedicada) e conformidade (LGPD com retenção zero de dados), o projeto maximiza sua probabilidade de sucesso e entrega uma solução de altíssimo valor no encerramento do Projeto Aplicado.

