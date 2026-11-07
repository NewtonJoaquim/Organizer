from enum import Enum
from pydantic import BaseModel, Field


class SortDirection(str, Enum):
    ASC = "ASC"    # Ordem crescente / do mais antigo ao mais recente / A-Z
    DESC = "DESC"  # Ordem decrescente / do mais recente ao mais antigo / Z-A


class NullsPosition(str, Enum):
    FIRST = "first"
    LAST = "last"


class SortCriterion(BaseModel):
    column: str | None = Field(
        default=None,
        description="Nome da coluna canônica ou original sobre a qual o ordenamento escalar será aplicado.",
    )
    custom_order: list[str] | None = Field(
        default=None,
        description="Lista ordenada de valores para ordenação categórica/ordinal personalizada não-alfabética.",
    )
    indicator_columns: list[str] | None = Field(
        default=None,
        description=(
            "Lista ordenada de colunas indicadoras (one-hot/matriz de presença) que representam uma escala ordinal "
            "ou categorias mutuamente exclusivas distribuídas horizontalmente (ex.: ['PP', 'P', 'M'] ou ['Ruim', 'Bom'])."
        ),
    )
    direction: SortDirection = Field(default=SortDirection.ASC, description="Direção da ordenação (ASC ou DESC).")
    nulls_position: NullsPosition = Field(default=NullsPosition.LAST, description="Posição de valores nulos ou vazios.")


class SortSpec(BaseModel):
    criteria: list[SortCriterion] = Field(
        default_factory=list,
        description="Lista ordenada de critérios de ordenação estável (mergesort).",
    )
    raw_instruction: str | None = Field(
        default=None,
        description="Comando original digitado pelo usuário em linguagem natural.",
    )
    explanation: str = Field(
        ...,
        description="Explicação concisa em português de como a instrução foi interpretada formalmente.",
    )


class ColumnMapping(BaseModel):
    original_column: str = Field(..., description="Nome bruto da coluna extraído da planilha.")
    canonical_column: str = Field(..., description="Nome canônico padronizado inferido pela IA (snake_case).")
    detected_type: str = Field(
        ...,
        description="Tipo de dado semântico inferido (ex.: date, currency, text, integer, percentage, id).",
    )
    confidence: float = Field(
        ...,
        description="Score de confiança do mapeamento semântico (0.0 a 1.0).",
    )
    semantic_reasoning: str = Field(
        ...,
        description="Justificativa sucinta para a padronização do termo e sinonímia detectada.",
    )


class MappingProposal(BaseModel):
    domain_detected: str = Field(
        ...,
        description="Domínio corporativo inferido (Financeiro, Vendas, Logística, RH, Confecção, Geral).",
    )
    mappings: list[ColumnMapping] = Field(
        ...,
        description="Lista de de-para para cada coluna informada nos metadados.",
    )
    sort_spec: SortSpec | None = Field(
        default=None,
        description="Especificação formal de ordenação se uma instrução de ordenamento tiver sido fornecida.",
    )
    estimated_prompt_tokens: int = Field(
        ...,
        description="Contagem de tokens do prompt de metadados.",
    )
    estimated_completion_tokens: int = Field(
        ...,
        description="Contagem de tokens da saída estruturada gerada.",
    )
    total_tokens: int = Field(
        ...,
        description="Total de tokens consumidos na inferência (deve ser < 800 tokens conforme RNF-04).",
    )


class SemanticOrchestratorRequest(BaseModel):
    columns: list[str] = Field(
        ...,
        description="Lista exclusiva dos nomes das colunas (metadados). Nenhuma linha de dados sensíveis permitida (RN-01).",
    )
    user_instruction: str | None = Field(
        default=None,
        description="Instrução opcional em português corrente (ex.: 'ordenar por data decrescente e valor').",
    )
    domain_hint: str | None = Field(
        default=None,
        description="Dica contextual opcional do segmento corporativo.",
    )


class SemanticOrchestratorResponse(BaseModel):
    proposal: MappingProposal
    metadata_only_compliance: bool = Field(
        default=True,
        description="Garantia formal de conformidade com RN-01 e LGPD (Zero Data Retention / Metadados exclusivos).",
    )
    processing_time_ms: float = Field(
        ...,
        description="Tempo de processamento da orquestração em milissegundos.",
    )
