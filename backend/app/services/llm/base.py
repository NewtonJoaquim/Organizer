from abc import ABC, abstractmethod
from app.schemas.semantic import MappingProposal, MultiSheetMappingProposal


class BaseLLMProvider(ABC):
    """Contrato abstrato para provedores de LLM com Saídas Estruturadas (Structured Outputs)."""

    @abstractmethod
    async def generate_mapping_proposal(
        self,
        columns: list[str],
        instruction: str | None = None,
        domain_hint: str | None = None,
    ) -> MappingProposal:
        """
        Gera uma proposta de mapeamento semântico canônico e especificação de ordenação
        estritamente a partir dos metadados fornecidos (sem dados das linhas).
        """
        pass

    @abstractmethod
    async def generate_multi_sheet_mapping_proposal(
        self,
        sheets: dict[str, list[str]],
        instruction: str | None = None,
        domain_hint: str | None = None,
    ) -> MultiSheetMappingProposal:
        """
        Gera uma proposta unificada de mapeamento semântico para múltiplas abas,
        alinhando colunas sinônimas em nomes canônicos idênticos sem duplicação de schema.
        """
        pass

