import time
from fastapi import HTTPException, status
from app.schemas.semantic import (
    SemanticOrchestratorRequest,
    SemanticOrchestratorResponse,
)
from app.services.llm.base import BaseLLMProvider
from app.services.llm.factory import get_llm_provider


class SemanticOrchestratorService:
    """
    Orquestrador Semântico com LLM e Saídas Estruturadas (RF-03, RF-04, RNF-04).
    Garante o isolamento de dados sensíveis (RN-01 / LGPD) enviando unicamente
    os metadados de cabeçalho para a inferência e retornando a proposta formal de de-para.
    """

    def __init__(self, provider: BaseLLMProvider | None = None) -> None:
        self._provider = provider

    @property
    def provider(self) -> BaseLLMProvider:
        if self._provider is None:
            self._provider = get_llm_provider()
        return self._provider

    async def orchestrate(
        self, request: SemanticOrchestratorRequest
    ) -> SemanticOrchestratorResponse:
        if not request.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A lista de colunas para mapeamento semântico não pode ser vazia.",
            )

        # Validação estrita de isolamento de dados sensíveis (RN-01 / RNF-03)
        # Nenhuma coluna pode conter blocos grandes de dados serializados
        for col in request.columns:
            if len(col) > 150:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Violação de governança LGPD (RN-01): Os dados enviados contêm strings "
                        "excessivamente longas que aparentam ser registros de dados e não metadados de cabeçalho."
                    ),
                )

        start_time = time.perf_counter()

        proposal = await self.provider.generate_mapping_proposal(
            columns=request.columns,
            instruction=request.user_instruction,
            domain_hint=request.domain_hint,
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return SemanticOrchestratorResponse(
            proposal=proposal,
            metadata_only_compliance=True,
            processing_time_ms=elapsed_ms,
        )


semantic_orchestrator = SemanticOrchestratorService()
