import json
import httpx
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.semantic import MappingProposal, MultiSheetMappingProposal
from app.services.llm.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Provedor para Google Gemini API com Structured Outputs."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

    async def generate_mapping_proposal(
        self,
        columns: list[str],
        instruction: str | None = None,
        domain_hint: str | None = None,
    ) -> MappingProposal:
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GEMINI_API_KEY não configurada no ambiente.",
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        prompt = (
            f"Receba a lista de colunas (metadados): {columns}\n"
            f"Instrução: {instruction or 'Padronizar e organizar'}\n"
            f"Dica de domínio: {domain_hint or 'Detectar automaticamente'}\n"
            "Retorne o mapeamento canônico em snake_case e especificação de ordenação sem incluir dados de linhas."
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "response_schema": MappingProposal.model_json_schema(),
                "temperature": 0.0,
                "maxOutputTokens": settings.MAX_TOKENS_PER_CALL,
            },
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Falha na API Gemini: HTTP {resp.status_code} - {resp.text}",
                )

            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_text)

            meta = data.get("usageMetadata", {})
            parsed["estimated_prompt_tokens"] = meta.get("promptTokenCount", 0)
            parsed["estimated_completion_tokens"] = meta.get("candidatesTokenCount", 0)
            parsed["total_tokens"] = meta.get("totalTokenCount", 0)

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
                detail="GEMINI_API_KEY não configurada no ambiente.",
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        prompt = (
            f"Receba as abas e suas respectivas colunas (metadados): {sheets}\n"
            f"Instrução: {instruction or 'Consolidar abas e alinhar colunas'}\n"
            f"Dica de domínio: {domain_hint or 'Detectar automaticamente'}\n"
            "Retorne o mapeamento canônico de cada aba, garantindo que colunas equivalentes recebam o mesmo nome canônico."
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "response_schema": MultiSheetMappingProposal.model_json_schema(),
                "temperature": 0.0,
                "maxOutputTokens": settings.MAX_TOKENS_PER_CALL,
            },
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Falha na API Gemini: HTTP {resp.status_code} - {resp.text}",
                )

            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_text)

            meta = data.get("usageMetadata", {})
            parsed["estimated_prompt_tokens"] = meta.get("promptTokenCount", 0)
            parsed["estimated_completion_tokens"] = meta.get("candidatesTokenCount", 0)
            parsed["total_tokens"] = meta.get("totalTokenCount", 0)

            return MultiSheetMappingProposal(**parsed)

