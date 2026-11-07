from abc import ABC, abstractmethod
from app.schemas.semantic import MappingProposal


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
