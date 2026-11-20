# Organizer App — Suplemento Nativo para Microsoft Excel (Add-in)

**Requisito Atendido:** `RF-10` — Prototipação de Suplemento Nativo (Microsoft Excel Add-in)  
**Tarefa Técnica:** `TSK-S3-01` (5 Story Points - Inovação / Alta)  
**Instituição:** XP Educação (XPE) — Pós-Graduação em Inteligência Artificial e Engenharia de Software  
**Data:** Novembro de 2026  

---

## 📌 Visão Geral da Solução

O **Suplemento Nativo (Office Add-in)** do **Organizer App** permite que analistas de negócios, coordenadores contábeis e gestores corporativos manipulem, padronizem e ordenem tabelas com auxílio de Inteligência Artificial **diretamente dentro do Microsoft Excel (Desktop e Web)**, sem a necessidade de alternar de telas, abrir navegadores externos ou exportar arquivos manualmente.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MICROSOFT EXCEL (365 / DESKTOP)                 │
│                                                                        │
│   [Planilha Ativa]                        [Painel Lateral - Taskpane]   │
│   ┌──────┬──────────┬────────┐           ┌────────────────────────────┐│
│   │ Ped  │ Cliente  │ Valor  │           │ ⚡ Organizer AI            ││
│   ├──────┼──────────┼────────┤           │ [1] Seleção Ativa [A1:C10] ││
│   │ #102 │ Alfa S/A │ 850,00 │ <───────> │ [2] "Ordenar por data e    ││
│   │ #101 │ Beta Ltd │ 320,00 │ Office.js │      maior valor"          ││
│   └──────┴──────────┴────────┘           │ [3] [Organizar Células]    ││
│                                          └─────────────┬──────────────┘│
└────────────────────────────────────────────────────────┼───────────────┘
                                                         │
                                             HTTP JSON   │ (Apenas Metadados
                                             Port 8000   │  ou Células Locais)
                                                         ▼
                                          ┌──────────────────────────────┐
                                          │   BACKEND RESTful LOCAL      │
                                          │   • /api/semantic/map (LLM)  │
                                          │   • /api/process/direct      │
                                          │     (Pandas Mergesort Local) │
                                          └──────────────────────────────┘
```

---

## 🛠️ Critérios da Definição de Pronto (Definition of Done - DoD)

- [x] **Estruturação do Manifesto XML (`manifest.xml`):** Em conformidade com o schema oficial `TaskPaneApp` (v1.1) da Microsoft, com botões integrados na Guia Início (*Home Tab*) da Faixa de Opções (*Ribbon*), ícones em alta resolução (16px, 32px e 80px) e permissão `ReadWriteDocument`.
- [x] **Painel Lateral Web Responsivo (`taskpane.html`):** Desenvolvido com tipografia corporativa (*Inter*), design system responsivo para painéis laterais de 320px a 450px, entrada em linguagem natural e atalhos rápidos (*templates*) para as personas mapeadas.
- [x] **Comunicação Bidirecional via Office JavaScript API (`taskpane.js`):**
  - Leitura das células selecionadas com `context.workbook.getSelectedRange()` ou da planilha completa com `getActiveWorksheet().getUsedRange()`.
  - Envio dos metadados para a API FastAPI (`/api/semantic/map` e `/api/process/direct`).
  - Escrita dos dados ordenados de volta na planilha ativa ou criação automática de nova aba limpa (`Organizer_Resultado`) com formatação em negrito, fundo azul corporativo (`#1E3A8A`) e auto-fit de colunas.
- [x] **Garantia Matemática de Integridade (RNF-02):** Auditoria em tempo real com hash multiset SHA-256 e garantia de 100% de integridade matemática (zero dados alucinados).
- [x] **Emulador Standalone Integrado:** Capacidade de ser executado e testado em qualquer navegador web moderno com amostras reais pré-carregadas das três personas (**Carlos**, **Mariana** e **Rodrigo**).

---

## 🚀 Como Executar e Testar Localmente

### 1. Iniciar o Backend da Aplicação
Certifique-se de que o backend FastAPI esteja em execução na porta 8000:
```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

### 2. Iniciar o Servidor do Suplemento (Porta 3000)
Em outro terminal:
```bash
cd excel-addin
python serve.py
```
O servidor inicializará exibindo a URL do painel:  
`https://localhost:3000/src/taskpane.html` (ou `http://localhost:3000/src/taskpane.html`)

---

## 💻 Instruções de Sideloading no Microsoft Excel

### Opção A: No Microsoft Excel na Web (Office 365 Online — Recomendado)
1. Acesse [https://office.com](https://office.com) e abra uma nova pasta de trabalho no **Excel na Web**.
2. Clique na guia **Inserir** (*Insert*) no menu superior.
3. Clique em **Suplementos** (*Add-ins*) ➔ **Mais Suplementos** (*Get Add-ins*).
4. Selecione a aba **Meus Suplementos** (*My Add-ins*) e clique em **Carregar Meu Suplemento** (*Upload My Add-in*).
5. Selecione o arquivo `manifest.xml` localizado na pasta `excel-addin/`.
6. O botão **Organizer AI** aparecerá imediatamente na guia **Início** (*Home*) da Faixa de Opções!

### Opção B: No Microsoft Excel Desktop (Windows)
1. Compartilhe a pasta `c:\Projetos\projeto-aplicado\excel-addin` na rede local como um compartilhamento de rede do Windows (`\\localhost\excel-addin`).
2. No Excel Desktop, vá em **Arquivo** ➔ **Opções** ➔ **Central de Confiabilidade** ➔ **Configurações da Central de Confiabilidade** ➔ **Catálogos de Suplementos Confiáveis**.
3. Adicione a URL do compartilhamento de rede (`\\localhost\excel-addin`) e marque a caixa **Mostrar no Menu**.
4. Reinicie o Excel. Em **Inserir** ➔ **Meus Suplementos** ➔ **Pasta Compartilhada**, selecione o **Organizer App**.

### Opção C: Teste Rápido no Navegador (Modo Standalone / Demonstração)
Abra diretamente a URL no Google Chrome ou Microsoft Edge:
```
http://localhost:3000/src/taskpane.html
```
O suplemento detectará automaticamente o ambiente web standalone e ativará o **Emulador Interativo com Datasets das Personas**:
- Botão **Amostra Confecção (Carlos)**: Testa grades e tamanhos de uniformes (PP a XG).
- Botão **Amostra Extrato (Mariana)**: Testa conciliação bancária de múltiplos bancos e ordenação por data/valor.
- Botão **Amostra Fretes (Rodrigo)**: Testa comparação de fretes, prazos e custos logísticos por KG.
