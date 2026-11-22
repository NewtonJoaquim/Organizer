FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir cryptography

COPY . .

EXPOSE 3000

ENV HOST=0.0.0.0
ENV PORT=3000
ENV PYTHONUNBUFFERED=1

CMD ["python", "serve.py"]
