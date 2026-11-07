from fastapi import APIRouter, status
from app.schemas.semantic import (
    SemanticOrchestratorRequest,
    SemanticOrchestratorResponse,
)
from app.services.semantic_orchestrator import semantic_orchestrator

router = APIRouter(prefix="/semantic", tags=["Orquestrador Semântico com LLM"])


@router.post(
    "/map",
    response_model=SemanticOrchestratorResponse,
    status_code=status.HTTP_200_OK,
    summary="Mapeamento semântico de schema e parser de comandos em linguagem natural (RF-03, RF-04)",
    description=(
        "Recebe estritamente a lista de nomes das colunas identificadas e a instrução textual "
        "do usuário. Envia apenas metadados para a inferência com saídas estruturadas Pydantic "
        "(MappingProposal e SortSpec), garantindo Zero Data Retention e consumo inferior a 800 tokens."
    ),
)
async def map_semantics(request: SemanticOrchestratorRequest) -> SemanticOrchestratorResponse:
    return await semantic_orchestrator.orchestrate(request)
