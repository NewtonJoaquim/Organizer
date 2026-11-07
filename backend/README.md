# Organizer App — Backend REST API

Módulo backend da solução **Organizer App**, desenvolvido em Python 3.11+ utilizando FastAPI, Pandas, Pydantic e gerenciamento ágil de dependências com `uv`.

## 📦 Arquitetura do Backend

```text
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── upload.py        # Endpoints POST /api/upload e DELETE /api/upload/{file_id}
│   │   │   └── inspect.py       # Endpoint POST /api/inspect/headers (Detecção Heurística)
│   │   └── routes.py            # Roteador central e Healthcheck
│   ├── core/
│   │   ├── config.py            # Variáveis de ambiente e regras de negócio (Pydantic Settings)
│   │   └── security.py          # Sanitização contra Path Traversal e validação de Magic Bytes
│   ├── schemas/
│   │   ├── upload.py            # Modelos Pydantic de entrada e saída de upload
│   │   └── header.py            # Modelos Pydantic para resultados de detecção de cabeçalho
│   ├── services/
│   │   ├── file_service.py      # Gerenciamento de armazenamento temporário isolado e expurgo (TTL)
│   │   └── header_detector.py   # Algoritmo heurístico de detecção de cabeçalhos (RF-02 / RN-03)
│   └── main.py                  # Instância da aplicação FastAPI e middlewares (CORS)
├── storage/
│   └── temp/                    # Diretório isolado para uploads temporários (Zero Retention)
├── tests/
│   ├── fixtures/
│   │   └── 2_SERIE_NATAL.xlsx   # Planilha corporativa real de validação da persona Carlos
│   ├── conftest.py              # Fixtures com geração de planilhas .xlsx e .xls em memória
│   ├── test_upload.py           # Suíte de testes automatizados de ingestão
│   └── test_header_detector.py  # Suíte de testes do algoritmo heurístico
└── pyproject.toml               # Configuração do projeto e dependências
```

---

## 🚀 Como Executar o Backend Localmente

### 1. Pré-requisitos
- Python 3.11 ou superior
- `uv` (gerenciador de pacotes ultrarrápido)

### 2. Instalação de Dependências
```bash
cd backend
uv sync --extra dev
```

### 3. Inicialização do Servidor de Desenvolvimento
```bash
uv run uvicorn app.main:app --reload --port 8000
```
- **Documentação Swagger UI:** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **Documentação ReDoc:** [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)
- **Healthcheck:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 🧪 Execução dos Testes Automatizados

```bash
cd backend
uv run pytest -v
```

### Casos de Teste Cobertos:
- ✅ `test_health_check`: Verificação de status operacional da API.
- ✅ `test_upload_valid_xlsx`: Upload e validação de planilha `.xlsx` real.
- ✅ `test_upload_valid_xls`: Upload e validação de planilha legada `.xls` (CFB/OLE2).
- ✅ `test_upload_file_size_exceeds_limit`: Rejeição estrita com `HTTP 413` para arquivos $> 20$ MB.
- ✅ `test_upload_invalid_extension`: Rejeição com `HTTP 400` para extensões perigosas ou não suportadas.
- ✅ `test_upload_path_traversal_sanitization`: Sanitização contra nomes maliciosos (`../../etc/passwd.xlsx`).
- ✅ `test_upload_corrupt_magic_bytes`: Detecção e rejeição de arquivos renomeados fraudulentamente.
- ✅ `test_upload_empty_file`: Rejeição de uploads vazios (0 bytes).
- ✅ `test_cleanup_file_success_and_not_found`: Descarte imediato e garantia de Zero Data Retention.
