import json
import httpx
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.semantic import MappingProposal
from app.services.llm.base import BaseLLMProvider


SYSTEM_PROMPT = """Você é o Orquestrador Semântico do Organizer App, um sistema corporativo de engenharia de dados.
Sua função é receber EXCLUSIVAMENTE a lista de nomes das colunas de uma planilha (metadados) e uma instrução em linguagem natural.
Em NENHUMA hipótese dados sensíveis de clientes ou valores de linhas serão fornecidos (conformidade estrita com LGPD e Zero Data Retention).

Você deve retornar estritamente um JSON estruturado aderente ao schema solicitado:
1. domain_detected: Segmento de negócio (Financeiro, Vendas, Logística, RH, Confecção ou Geral).
2. mappings: Para cada coluna original, o nome canônico em snake_case (ex: data_vencimento), tipo de dado inferido e pontuação de confiança (0.0 a 1.0).
3. sort_spec: Se o usuário pedir ordenação, converter em critérios formais (coluna, direção ASC/DESC).
"""


class OpenAIProvider(BaseLLMProvider):
    """Provedor para OpenAI ou APIs compatíveis (Groq, vLLM, Ollama, etc.) com Structured Outputs."""

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.base_url = (base_url or settings.OPENAI_BASE_URL or "https://api.openai.com/v1").rstrip("/")

    async def generate_mapping_proposal(
        self,
        columns: list[str],
        instruction: str | None = None,
        domain_hint: str | None = None,
    ) -> MappingProposal:
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OPENAI_API_KEY não configurada no ambiente.",
            )

        user_content = {
            "columns": columns,
            "instruction": instruction or "Organizar e padronizar os nomes de colunas",
            "domain_hint": domain_hint,
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_content, ensure_ascii=False)},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "mapping_proposal",
                    "strict": True,
                    "schema": MappingProposal.model_json_schema(),
                },
            },
            "max_tokens": settings.MAX_TOKENS_PER_CALL,
            "temperature": 0.0,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Falha na chamada à API de LLM: HTTP {resp.status_code} - {resp.text}",
                )

            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            parsed = json.loads(raw_text)
            # Atualiza contagem real de tokens informada pela API
            parsed["estimated_prompt_tokens"] = usage.get("prompt_tokens", 0)
            parsed["estimated_completion_tokens"] = usage.get("completion_tokens", 0)
            parsed["total_tokens"] = usage.get("total_tokens", 0)

            return MappingProposal(**parsed)
