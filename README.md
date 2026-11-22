# Organizer App — Organizador Inteligente de Dados e Planilhas

**Projeto Aplicado:** Pós-Graduação em Inteligência Artificial e Engenharia de Software  
**Instituição:** XP Educação (XPE)  
**Autor:** Newton Joaquim  
**Ano:** 2026  

---

## 🚀 Como Subir Toda a Aplicação com um Único Comando

O ecossistema do **Organizer App** é composto por três módulos integrados:
1. **Backend RESTful:** FastAPI + Pandas + Orquestrador LLM (porta `8000`)
2. **Frontend Web:** Aplicação SPA em React 19 + TypeScript + Tailwind CSS (porta `5173`)
3. **Microsoft Excel Add-in:** Suplemento nativo via *Office JavaScript API* com suporte a emulador web (porta `3000`)

---

### Opção 1: Inicialização Nativa Rápida (Recomendada / Zero Dependências de Daemon)

Você pode subir todos os três serviços simultaneamente com **qualquer um** dos comandos abaixo a partir da raiz do repositório:

```bash
# Via Python (Multiplataforma)
python start.py

# OU via npm
npm start

# OU no Windows (CMD / Prompt)
start.bat

# OU no Windows (PowerShell)
.\start.ps1
```

O orquestrador `start.py`:
- Detecta automaticamente o ambiente virtual do backend (`.venv`) e o Node.js;
- Inicia o Backend, Frontend e Excel Add-in em paralelo com saída de logs unificada;
- Monitora a saúde das portas (`8000`, `5173` e `3000`);
- Exibe o dashboard com os links de acesso clicáveis;
- Trata `Ctrl+C` encerrando todos os subprocessos filhos sem deixar portas presas.

---

### Opção 2: Inicialização Containerizada via Docker Compose

Se o **Docker Desktop** estiver em execução na sua máquina, você pode subir toda a infraestrutura em contêineres isolados com:

```bash
docker compose up --build
```

Ou através do script com a flag `--docker`:
```bash
python start.py --docker
```

---

## 🧭 Painel de Acesso aos Serviços

Após a inicialização, os serviços estarão disponíveis nos seguintes endereços:

| Serviço | Endereço Local | Descrição |
| :--- | :--- | :--- |
| 🌐 **Frontend Web** | [http://localhost:5173](http://localhost:5173) | Interface gráfica com drag & drop, linguagem natural e preview Antes x Depois. |
| ⚡ **Backend REST API** | [http://localhost:8000/api/docs](http://localhost:8000/api/docs) | Documentação Swagger interativa com todos os endpoints e schemas Pydantic. |
| 📘 **ReDoc API** | [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc) | Documentação técnica dos contratos e endpoints da API. |
| 📊 **Excel Add-in (Taskpane)** | [https://localhost:3000/src/taskpane.html](https://localhost:3000/src/taskpane.html) | Painel lateral do suplemento Excel e Emulador Standalone com amostras das personas. |
| 📄 **Manifesto XML Add-in** | [https://localhost:3000/manifest.xml](https://localhost:3000/manifest.xml) | Manifesto para sideloading no Excel Desktop ou Excel na Web (Office 365). |

---

## ⚖️ Avaliação Técnica: Docker vs. Execução Nativa

| Critério | Execução Nativa (`python start.py`) | Containerização (`docker compose up`) |
| :--- | :--- | :--- |
| **Prontidão de Inicialização** | **Instantânea (~1 a 2 segundos)** | 30 a 60 segundos (build/download de imagens) |
| **Consumo de Memória (RAM)** | **Leve (~200 MB total)** | 2 GB a 4 GB (WSL2 / Vmmem no Windows) |
| **Dependência de Daemon** | **Zero (apenas Python e Node instalados)** | Requer Docker Desktop ativo |
| **Integração com Excel Desktop** | **Direta** (certificados locais e localhost) | Requer mapeamento de portas e bridge de rede |
| **Isolamento de Ambiente** | Médio (usa `.venv` local e `node_modules`) | **Máximo (contêineres Linux isolados)** |
| **Prontidão para Cloud (Deploy)** | Requer setup de VM / PaaS | **Pronto para Kubernetes, ECS ou GCP Cloud Run** |

> **Conclusão:** Para **demonstrações locais, avaliação de banca e testes de usabilidade**, a execução nativa via `python start.py` é mais ágil, leve e confiável (não depende do Docker Desktop estar aberto). Para **deploy em nuvem, ambientes de CI/CD e avaliação em máquinas heterogêneas**, o `docker-compose.yml` garante reprodutibilidade perfeita.

---

## 🧪 Execução dos Testes Automatizados

Para rodar a suíte completa de 62 testes unitários, de integração e de carga:

```bash
cd backend
uv run pytest -v
```
