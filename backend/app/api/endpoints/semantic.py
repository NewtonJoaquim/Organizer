from fastapi import APIRouter, status
from app.schemas.semantic import (
    MultiSheetSemanticRequest,
    MultiSheetSemanticResponse,
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


@router.post(
    "/map-multi-sheet",
    response_model=MultiSheetSemanticResponse,
    status_code=status.HTTP_200_OK,
    summary="Mapeamento semântico canônico unificado para múltiplas abas (RF-06)",
    description=(
        "Recebe os nomes e colunas de múltiplas abas de uma pasta de trabalho. "
        "Alinha colunas sinônimas em nomes canônicos idênticos para consolidação sem duplicidade de schema. "
        "Envia estritamente metadados de colunas (Zero Data Retention / RN-01)."
    ),
)
async def map_semantics_multi_sheet(
    request: MultiSheetSemanticRequest,
) -> MultiSheetSemanticResponse:
    return await semantic_orchestrator.orchestrate_multi_sheet(request)

