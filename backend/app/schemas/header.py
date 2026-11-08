from pydantic import BaseModel, Field


class HeaderDetectionResult(BaseModel):
    header_row_index: int = Field(
        ...,
        description="Índice da linha identificada como cabeçalho (base 0).",
    )
    data_start_row_index: int = Field(
        ...,
        description="Índice da primeira linha de dados após o cabeçalho (base 0).",
    )
    raw_columns: list[str] = Field(
        ...,
        description="Lista de valores literais extraídos da linha de cabeçalho.",
    )
    clean_columns: list[str] = Field(
        ...,
        description="Lista de nomes padronizados/sanitizados para uso em DataFrames.",
    )
    confidence_score: float = Field(
        ...,
        description="Pontuação heurística de confiança calculada para o cabeçalho (0.0 a 1.0).",
    )
    is_fallback: bool = Field(
        default=False,
        description="Indica se o algoritmo acionou o fallback para a linha 0 por confiança < 70% (RN-03).",
    )
    inspected_rows_count: int = Field(
        ...,
        description="Quantidade de linhas preliminares examinadas (máximo 15 por padrão).",
    )
    sheet_name: str = Field(
        ...,
        description="Nome da aba/planilha inspecionada.",
    )
    available_sheets: list[str] = Field(
        default_factory=list,
        description="Lista de todas as abas disponíveis na pasta de trabalho.",
    )
    warning_message: str | None = Field(
        default=None,
        description="Mensagem de alerta caso a confiança seja limítrofe ou em caso de fallback.",
    )


class InspectHeadersRequest(BaseModel):
    file_id: str = Field(..., description="UUID do arquivo previamente armazenado temporariamente")
    sheet_name: str | None = Field(default=None, description="Nome opcional da aba. Se omitido, usa a ativa/primeira.")


class WorkbookInspectionRequest(BaseModel):
    file_id: str = Field(..., description="UUID do arquivo previamente armazenado temporariamente")


class WorkbookInspectionResult(BaseModel):
    file_id: str = Field(..., description="UUID do arquivo inspecionado.")
    total_sheets: int = Field(..., description="Quantidade total de abas na pasta de trabalho.")
    sheet_names: list[str] = Field(..., description="Nomes de todas as abas disponíveis.")
    sheets: list[HeaderDetectionResult] = Field(
        ...,
        description="Resultados da inspeção heurística de cada uma das abas.",
    )

