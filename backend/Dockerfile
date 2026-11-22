FROM python:3.12-slim

WORKDIR /app

# Instala curl para healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copia binário oficial do uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copia arquivos de dependência
COPY pyproject.toml uv.lock ./

# Instala dependências em ambiente virtual isolado
RUN uv sync --frozen --no-dev

# Garante que o ambiente virtual está no PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Copia código-fonte da aplicação
COPY app/ ./app/

# Cria diretório de armazenamento temporário (Zero Data Retention)
RUN mkdir -p /app/storage/temp

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
