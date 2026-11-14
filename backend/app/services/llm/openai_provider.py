import json
import httpx
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.semantic import MappingProposal, MultiSheetMappingProposal
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
        "column": "nome_coluna_ou_null",
        "custom_order": ["val1", "val2"] ou null,
        "indicator_columns": ["col1", "col2"] ou null,
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
- Mantenha 'semantic_reasoning' extremamente sucinto (máximo 10 palavras por coluna) para economia de tokens.
- Se não houver instrução de ordenação, defina sort_spec como null.
- Mantenha canonical_column sempre em snake_case limpo e padronizado em português.
- Matrizes Indicadoras / One-Hot (agnóstico): Quando o usuário pedir ordenação por uma dimensão que está distribuída horizontalmente em múltiplas colunas de presença/opção mútua (ex.: tamanhos PP..XXG em confecção, escala de notas Péssimo..Excelente em pesquisas, faixas etárias, prioridades), utilize 'indicator_columns' com a lista ordenada dessas colunas na sequência semântica correta (ex: indicator_columns=['PP', 'P', 'M', 'G', 'GG', 'XG', 'XXG']).
- Ordenação Categórica Não-Alfabética: Se a coluna for única mas seus valores seguirem uma ordem não-alfabética (ex.: Baixo/Médio/Alto), defina 'custom_order' com a sequência ordinal correta.
"""


MULTI_SHEET_SYSTEM_PROMPT = """Você é o Orquestrador Semântico Multi-Abas do Organizer App, um sistema corporativo de engenharia de dados.
Sua função é receber EXCLUSIVAMENTE os nomes das abas e as listas de nomes de colunas de uma pasta de trabalho (metadados) e uma instrução opcional do usuário.
Em NENHUMA hipótese dados sensíveis de clientes ou valores de linhas serão fornecidos (conformidade estrita com LGPD e Zero Data Retention).

Você deve mapear as colunas de cada aba para nomes canônicos padronizados.
MUITO IMPORTANTE: Colunas que representam a mesma informação em abas diferentes (ex.: 'Data Movimento' em uma aba e 'Data' em outra, ou 'Valor R$' e 'Valor') DEVEM RECEBER EXATAMENTE O MESMO canonical_column, para que a consolidação vertical alinhe as colunas sem duplicar o schema.

Você deve retornar OBRIGATORIAMENTE um objeto JSON estritamente com a seguinte estrutura:
{
  "domain_detected": "Financeiro" | "Vendas" | "Logística" | "RH" | "Confecção" | "Geral",
  "sheet_mappings": {
    "Nome_Aba_1": [
      {
        "original_column": "Nome_Original",
        "canonical_column": "nome_canonico_em_snake_case",
        "detected_type": "date" | "currency" | "text" | "integer" | "numeric" | "id",
        "confidence": 0.95
      }
    ]
  },
  "unified_canonical_columns": ["coluna_1", "coluna_2"],
  "sort_spec": {
    "criteria": [
      {
        "column": "coluna_canonica_ou_null",
        "custom_order": ["val1", "val2"] ou null,
        "indicator_columns": ["col1", "col2"] ou null,
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
- NÃO inclua o campo 'semantic_reasoning' nos mapeamentos de colunas para economia de tokens e concisão estrita.
- Se não houver instrução de ordenação, defina sort_spec como null.
- Mantenha canonical_column sempre em snake_case limpo e padronizado em português.
- Matrizes Indicadoras / One-Hot (agnóstico): Quando o usuário pedir ordenação por uma dimensão que está distribuída horizontalmente em múltiplas colunas de presença/opção mútua (ex.: tamanhos PP..XXG em confecção, escala de notas Péssimo..Excelente em pesquisas, faixas etárias, prioridades), utilize 'indicator_columns' com a lista ordenada dessas colunas na sequência semântica correta (ex: indicator_columns=['PP', 'P', 'M', 'G', 'GG', 'XG', 'XXG']).
- Ordenação Categórica Não-Alfabética: Se a coluna for única mas seus valores seguirem uma ordem não-alfabética (ex.: Baixo/Médio/Alto), defina 'custom_order' com a sequência ordinal correta.
"""


class OpenAIProvider(BaseLLMProvider):
    """Provedor para OpenAI (GPT-4o-mini) com saídas estruturadas JSON validadas via Pydantic."""

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.base_url = (base_url or settings.OPENAI_BASE_URL or "https://api.openai.com/v1").rstrip("/")

    @staticmethod
    def _clean_json_markdown(text: str) -> str:
        s = text.strip()
        if s.startswith("```json"):
            s = s[7:]
        elif s.startswith("```"):
            s = s[3:]
        if s.endswith("```"):
            s = s[:-3]
        return s.strip()

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
            "max_tokens": max(4096, settings.MAX_TOKENS_PER_CALL),
            "temperature": 0.0,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
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
            choice = data["choices"][0]
            if choice.get("finish_reason") == "length":
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="A resposta do modelo de IA atingiu o limite de tokens antes de concluir o mapeamento. Simplifique a instrução.",
                )

            raw_text = choice["message"]["content"]
            usage = data.get("usage", {})

            cleaned_text = self._clean_json_markdown(raw_text)
            try:
                parsed = json.loads(cleaned_text)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Resposta da IA não pôde ser interpretada como JSON: {exc}",
                ) from exc

            parsed["estimated_prompt_tokens"] = usage.get("prompt_tokens", 0)
            parsed["estimated_completion_tokens"] = usage.get("completion_tokens", 0)
            parsed["total_tokens"] = usage.get("total_tokens", 0)

            return MappingProposal(**parsed)

    async def generate_multi_sheet_mapping_proposal(
        self,
        sheets: dict[str, list[str]],
        instruction: str | None = None,
        domain_hint: str | None = None,
    ) -> MultiSheetMappingProposal:
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OPENAI_API_KEY não configurada no ambiente ou no arquivo .env.",
            )

        user_content = {
            "sheets": sheets,
            "instruction": instruction or "Consolidar as abas e padronizar os nomes de colunas",
            "domain_hint": domain_hint,
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": MULTI_SHEET_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_content, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": max(4096, settings.MAX_TOKENS_PER_CALL),
            "temperature": 0.0,
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
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
            choice = data["choices"][0]
            if choice.get("finish_reason") == "length":
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="A resposta do modelo de IA atingiu o limite de tokens antes de concluir o mapeamento multi-abas. Tente consolidar menos abas simultâneas ou simplificar a instrução.",
                )

            raw_text = choice["message"]["content"]
            usage = data.get("usage", {})

            cleaned_text = self._clean_json_markdown(raw_text)
            try:
                parsed = json.loads(cleaned_text)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"A resposta gerada pela IA não pôde ser interpretada como JSON válido: {exc}. Saída truncada ou corrompida.",
                ) from exc

            parsed["estimated_prompt_tokens"] = usage.get("prompt_tokens", 0)
            parsed["estimated_completion_tokens"] = usage.get("completion_tokens", 0)
            parsed["total_tokens"] = usage.get("total_tokens", 0)

            return MultiSheetMappingProposal(**parsed)

