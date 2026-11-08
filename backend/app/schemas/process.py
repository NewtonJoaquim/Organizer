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


class SheetIntegrityAudit(BaseModel):
    sheet_name: str = Field(..., description="Nome da aba auditada.")
    pre_process_row_count: int = Field(..., description="Linhas originais da aba.")
    post_process_row_count: int = Field(..., description="Linhas da aba presentes na tabela consolidada.")
    pre_process_hash: str = Field(..., description="Hash SHA-256 multiset dos dados originais da aba.")
    post_process_hash: str = Field(..., description="Hash SHA-256 multiset dos dados da aba na tabela final.")
    integrity_verified: bool = Field(..., description="100% de correspondência sem perda ou alteração.")


class MultiSheetIntegrityAudit(BaseModel):
    total_pre_process_row_count: int = Field(..., description="Soma total de linhas de todas as abas consolidadas.")
    total_post_process_row_count: int = Field(..., description="Total de linhas da tabela consolidada final.")
    rows_match: bool = Field(..., description="Verificação de que nenhuma linha foi perdida ou criada.")
    per_sheet_audit: dict[str, SheetIntegrityAudit] = Field(
        ...,
        description="Auditoria detalhada e isolada por aba individual.",
    )
    integrity_verified: bool = Field(..., description="Garantia estrita de integridade matemática (RNF-02).")


class ConsolidateSheetsRequest(BaseModel):
    file_id: str = Field(..., description="ID do arquivo previamente armazenado temporariamente.")
    sheet_names: list[str] | None = Field(
        default=None,
        description="Lista de nomes das abas a consolidar. Se omitido ou null, consolida todas as abas do arquivo.",
        json_schema_extra={"example": None},
    )
    header_row_indices: dict[str, int | None] | None = Field(
        default=None,
        description="Dicionário opcional de índices de cabeçalho por aba (base 0). Se omitido, utiliza detecção heurística em cada aba.",
        json_schema_extra={"example": None},
    )
    column_mappings: dict[str, dict[str, str]] | dict[str, str] | None = Field(
        default=None,
        description=(
            "Mapeamento de-para de colunas para nomes canônicos. Pode ser especificado por aba "
            "({'Janeiro': {'Data Mov': 'data'}, 'Fevereiro': {'Data': 'data'}}) ou como dicionário global unificado."
        ),
        json_schema_extra={"example": None},
    )
    add_source_column: bool = Field(
        default=True,
        description="Adiciona coluna indicando a aba de origem de cada linha (RF-06).",
    )
    source_column_name: str = Field(
        default="aba_origem",
        description="Nome da coluna que identifica a aba de origem dos dados.",
    )
    sort_spec: SortSpec | None = Field(
        default=None,
        description="Especificação formal de ordenação multi-critério sobre os dados consolidados.",
    )
    keep_original_headers: bool = Field(
        default=False,
        description="Se True, preserva os nomes originais de colunas da planilha em vez de aplicar column_mappings.",
    )
    consolidated_sheet_title: str = Field(
        default="Consolidado",
        description="Nome da aba de saída no arquivo Excel exportado.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "file_id": "uuid-do-arquivo",
                "sheet_names": None,
                "header_row_indices": None,
                "column_mappings": {
                    "Janeiro": {"Data Movimento": "data", "Histórico": "descricao", "Valor R$": "valor"},
                    "Fevereiro": {"Data": "data", "Descrição": "descricao", "Valor": "valor"},
                },
                "add_source_column": True,
                "source_column_name": "aba_origem",
                "keep_original_headers": False,
                "consolidated_sheet_title": "Consolidado",
                "sort_spec": None,
            }
        }
    }


class ConsolidateSheetsResponse(BaseModel):
    file_id: str = Field(..., description="ID do arquivo original de entrada.")
    processed_file_id: str = Field(..., description="UUID do arquivo consolidado gerado.")
    filename: str = Field(..., description="Nome do arquivo gerado para download.")
    download_url: str = Field(..., description="URL relativa para download da planilha consolidada.")
    sheets_consolidated: list[str] = Field(..., description="Lista de abas unificadas na consolidação.")
    rows_per_sheet: dict[str, int] = Field(..., description="Contagem de registros por aba original.")
    total_rows_consolidated: int = Field(..., description="Quantidade total de linhas na tabela consolidada.")
    columns: list[str] = Field(..., description="Lista final de colunas alinhadas da tabela consolidada.")
    integrity_audit: MultiSheetIntegrityAudit = Field(..., description="Evidência matemática de integridade estrita (RNF-02).")
    processing_time_ms: float = Field(..., description="Tempo de execução do merge determinístico em ms.")
    message: str = Field(default="Múltiplas abas consolidadas com sucesso sem duplicação de schema e com 100% de integridade matemática.")

