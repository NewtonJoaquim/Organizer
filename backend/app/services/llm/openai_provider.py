import json
import httpx
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.semantic import MappingProposal
from app.services.llm.base import BaseLLMProvider


SYSTEM_PROMPT = """Você é o Orquestrador Semântico do Organizer App, um sistema corporativo de engenharia de dados.
Sua função é receber EXCLUSIVAMENTE a lista de nomes das colunas de uma planilha (metadados) e uma instrução opcional do usuário.
Em NENHUMA hipótese dados sensíveis de clientes ou valores de linhas serão fornecidos (conformidade estrita com LGPD e Zero Data Retention).

Você deve retornar OBRIGATORIAMENTE um objeto JSON estritamente com a seguinte estrutura:
{
  "domain_detected": "Financeiro" | "Vendas" | "Logística" | "RH" | "Confecção" | "Geral",
  "mappings": [
    {
      "original_column": "Nome_Original",
      "canonical_column": "nome_canonico_em_snake_case",
      "detected_type": "date" | "currency" | "text" | "integer" | "numeric" | "id",
      "confidence": 0.95,
      "semantic_reasoning": "Justificativa breve de até 10 palavras"
    }
  ],
  "sort_spec": {
    "criteria": [
      {
        "column": "coluna_alvo",
        "direction": "ASC" | "DESC",
        "nulls_position": "last"
      }
    ],
    "raw_instruction": "instrução do usuário",
    "explanation": "Explicação concisa em português de como a instrução foi interpretada"
  },
  "estimated_prompt_tokens": 0,
  "estimated_completion_tokens": 0,
  "total_tokens": 0
}

Regras Cruciais:
- Mantenha 'semantic_reasoning' extremamente sucinto (máximo 10 palavras por coluna) para economia estrita de tokens.
- Se não houver instrução de ordenação, defina sort_spec como null.
- Mantenha canonical_column sempre em snake_case limpo e padronizado em português.
- Mapeamento por tamanho de peça/camisa em Confecção: quando a planilha tiver colunas dedicadas para cada tamanho (ex: PP, P, M, G, GG, XG, XXG ou grade_pp, grade_p, etc.) e o usuário pedir ordenação por tamanho de camisa/peça/grade, você DEVE gerar critérios no sort_spec na sequência natural de tamanhos têxteis (PP -> P -> M -> G -> GG -> XG -> XXG) com direction 'ASC' e nulls_position 'last'. Isso agrupa os registros por tamanho na ordem têxtil canônica mantendo a estabilidade.
"""


class OpenAIProvider(BaseLLMProvider):
    """Provedor para OpenAI (GPT-4o-mini) com saídas estruturadas JSON validadas via Pydantic."""

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
                detail="OPENAI_API_KEY não configurada no ambiente ou no arquivo .env.",
            )

        user_content = {
            "columns": columns,
            "instruction": instruction or "Padronizar os nomes de colunas e inferir os tipos semânticos",
            "domain_hint": domain_hint,
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_content, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": settings.MAX_TOKENS_PER_CALL,
            "temperature": 0.0,
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
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
                    detail=f"Falha na chamada à API de LLM da OpenAI: HTTP {resp.status_code} - {resp.text}",
                )

            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            parsed = json.loads(raw_text)
            parsed["estimated_prompt_tokens"] = usage.get("prompt_tokens", 0)
            parsed["estimated_completion_tokens"] = usage.get("completion_tokens", 0)
            parsed["total_tokens"] = usage.get("total_tokens", 0)

            return MappingProposal(**parsed)
