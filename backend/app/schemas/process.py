from pydantic import BaseModel, Field
from app.schemas.semantic import SortSpec


class IntegrityAudit(BaseModel):
    pre_process_row_count: int = Field(..., description="Contagem total de linhas de dados antes do processamento.")
    post_process_row_count: int = Field(..., description="Contagem total de linhas de dados após o processamento.")
    rows_match: bool = Field(..., description="Indica se a quantidade de linhas foi rigorosamente preservada.")
    pre_process_hash: str = Field(..., description="SHA-256 multiset das células de dados pré-processamento.")
    post_process_hash: str = Field(..., description="SHA-256 multiset das células de dados pós-processamento.")
    integrity_verified: bool = Field(
        ...,
        description="Garantia matemática estrita de 100% de integridade (zero dados alterados ou alucinados).",
    )


class ProcessSpreadsheetRequest(BaseModel):
    file_id: str = Field(..., description="ID do arquivo original previamente ingerido.")
    sheet_name: str | None = Field(default=None, description="Nome da aba a processar. Se omitido, usa a ativa.")
    header_row_index: int | None = Field(
        default=None,
        description="Índice da linha de cabeçalho (0-based). Deixe null ou omita para detecção automática inteligente.",
        json_schema_extra={"example": None},
    )
    sort_spec: SortSpec | None = Field(
        default=None,
        description="Especificação formal de ordenação gerada pelo orquestrador semântico (/api/semantic/map).",
    )
    column_mapping: dict[str, str] | None = Field(
        default=None,
        description="Dicionário opcional de de-para para renomeação canônica. Deixe null se quiser manter cabeçalhos originais.",
        json_schema_extra={"example": None},
    )
    keep_original_headers: bool = Field(
        default=False,
        description="Se True, preserva os nomes originais de colunas da planilha em vez de aplicar column_mapping.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "file_id": "uuid-do-arquivo",
                "sheet_name": "ALFA",
                "header_row_index": None,
                "keep_original_headers": True,
                "sort_spec": {
                    "criteria": [
                        {
                            "indicator_columns": ["PP", "P", "M", "G", "GG", "XG", "XXG"],
                            "direction": "ASC",
                            "nulls_position": "last",
                        }
                    ],
                    "raw_instruction": "Organize por tamanho das camisetas",
                    "explanation": "Ordenação por tamanho",
                },
                "column_mapping": None,
            }
        }
    }


class ProcessSpreadsheetResponse(BaseModel):
    file_id: str = Field(..., description="ID do arquivo original de entrada.")
    processed_file_id: str = Field(..., description="Novo UUID do arquivo limpo e ordenado gerado.")
    filename: str = Field(..., description="Nome do arquivo gerado para download.")
    download_url: str = Field(..., description="URL relativa para download do arquivo processado.")
    rows_processed: int = Field(..., description="Quantidade de registros de dados tratados.")
    columns: list[str] = Field(..., description="Lista final de nomes das colunas da planilha exportada.")
    integrity_audit: IntegrityAudit = Field(..., description="Evidência matemática de integridade estrita (RNF-02).")
    processing_time_ms: float = Field(..., description="Tempo de execução do processamento determinístico local em ms.")
    message: str = Field(default="Planilha processada e ordenada com 100% de integridade matemática.")
