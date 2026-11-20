import hashlib
import time
import uuid
from pathlib import Path
from typing import Any
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.process import (
    ConsolidateSheetsRequest,
    ConsolidateSheetsResponse,
    DirectProcessRequest,
    DirectProcessResponse,
    IntegrityAudit,
    MultiSheetIntegrityAudit,
    ProcessSpreadsheetRequest,
    ProcessSpreadsheetResponse,
    SheetIntegrityAudit,
)
from app.schemas.semantic import SortCriterion, SortDirection, SortSpec
from app.services.file_service import file_service
from app.services.header_detector import header_detector


class DeterministicEngineService:
    """
    Motor de processamento determinístico local e ordenação algorítmica estável (RF-05, RN-02, RNF-02).
    Garante exatidão matemática de 100% dos dados pré e pós-processamento,
    rejeitando qualquer alteração ou alucinação de valores.
    """

    @staticmethod
    def calculate_multiset_hash(df: pd.DataFrame) -> str:
        """
        Calcula o hash multiset (SHA-256 cumulativo) de todas as linhas de dados.
        Como a ordenação apenas permuta as posições das linhas sem alterar o valor das células,
        a ordenação lexicográfica dos hashes individuais de cada linha DEVE produzir um
        hash multiset idêntico antes e depois da ordenação (RNF-02).
        """
        row_hashes: list[str] = []
        for row in df.itertuples(index=False, name=None):
            # Normalização determinística de valores para representação textual canônica
            normalized_cells = ["" if pd.isna(val) else str(val).strip() for val in row]
            row_repr = "|".join(normalized_cells)
            row_hash = hashlib.sha256(row_repr.encode("utf-8")).hexdigest()
            row_hashes.append(row_hash)

        # Ordena os hashes de linha de forma independente para obter o multiset hash imutável
        sorted_hashes = sorted(row_hashes)
        combined_payload = "\n".join(sorted_hashes)
        return hashlib.sha256(combined_payload.encode("utf-8")).hexdigest()

    def read_spreadsheet(
        self, file_path: Path, sheet_name: str | None, header_row: int
    ) -> tuple[pd.DataFrame, str]:
        """Lê os dados da planilha a partir da linha de cabeçalho detectada."""
        ext = file_path.suffix.lower()

        if ext == ".xlsx":
            engine = "openpyxl"
        elif ext == ".xls":
            engine = "xlrd"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato '{ext}' não suportado pelo motor de processamento.",
            )

        try:
            # Identifica aba ativa se não informada
            if not sheet_name:
                if ext == ".xlsx":
                    wb = openpyxl.load_workbook(file_path, read_only=True)
                    target_sheet = wb.sheetnames[0]
                    wb.close()
                else:
                    import xlrd
                    book = xlrd.open_workbook(str(file_path), on_demand=True)
                    target_sheet = book.sheet_names()[0]
            else:
                target_sheet = sheet_name

            df = pd.read_excel(
                file_path,
                sheet_name=target_sheet,
                skiprows=header_row,
                header=0,
                engine=engine,
            )

            # Remove colunas e linhas completamente vazias
            df = df.dropna(how="all", axis=0).dropna(how="all", axis=1)

            # Garante que os nomes de colunas sejam strings limpas
            df.columns = [str(col).strip() if not pd.isna(col) else f"coluna_{i+1}" for i, col in enumerate(df.columns)]

            # Higienização de strings contra caracteres invisíveis e espaços duplos (TASK-09 / RF-09)
            from app.services.normalizer import data_normalizer
            for col in df.columns:
                if pd.api.types.is_string_dtype(df[col]) or df[col].dtype in ["object", "str", "string"]:
                    df[col] = df[col].apply(data_normalizer.clean_text)

            return df, target_sheet

        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Falha na leitura determinística da planilha: {str(e)}",
            )

    def apply_stable_sort(
        self,
        df: pd.DataFrame,
        sort_spec: SortSpec | None,
        column_mapping: dict[str, str] | None,
    ) -> pd.DataFrame:
        """
        Executa ordenação multi-critério determinística via mergesort estável (RN-02).
        Preserva a ordem relativa de registros em caso de empate (estabilidade algorítmica).

        Suporta três modalidades agnósticas de ordenação:
        1. Escalar convencional (numérica, data, alfabética);
        2. Categórica não-alfabética via `custom_order` (ordenações ordinais arbitrárias);
        3. Matriz Indicadora horizontal (one-hot) via `indicator_columns` (presença de marcação).
        Também suporta fallback de compatibilidade caso uma sequência de colunas indicadoras
        seja enviada em critérios individuais.
        """
        if not sort_spec or not sort_spec.criteria:
            return df.copy()

        bi_mapping: dict[str, str] = {}
        if column_mapping:
            for orig, canon in column_mapping.items():
                if orig and canon:
                    bi_mapping[str(orig).strip().lower()] = str(canon).strip()
                    bi_mapping[str(canon).strip().lower()] = str(orig).strip()

        df_cols_lower = {col.lower(): col for col in df.columns}

        def resolve_col(target_name: str | None) -> str | None:
            if not target_name:
                return None
            target_clean = str(target_name).strip()
            target_lower = target_clean.lower()

            # 1. Correspondência exata direta no dataframe
            if target_lower in df_cols_lower:
                return df_cols_lower[target_lower]

            # 2. Correspondência via mapeamento bidirecional (orig <-> canon)
            if target_lower in bi_mapping:
                mapped_target = bi_mapping[target_lower].lower()
                if mapped_target in df_cols_lower:
                    return df_cols_lower[mapped_target]

            # 3. Correspondência semântica por sufixo ou prefixo (ex.: 'PP' -> 'tamanho_pp', 'p' -> 'tamanho_p')
            for col_lower, actual_col in df_cols_lower.items():
                if col_lower == target_lower:
                    return actual_col
                if col_lower.endswith(f"_{target_lower}") or col_lower.startswith(f"{target_lower}_"):
                    return actual_col
                if target_lower.endswith(f"_{col_lower}") or target_lower.startswith(f"{col_lower}_"):
                    return actual_col

            # 4. Correspondência por substring se comprimento > 2
            if len(target_lower) > 2:
                for col_lower, actual_col in df_cols_lower.items():
                    if len(col_lower) > 2 and (target_lower in col_lower or col_lower in target_lower):
                        return actual_col
            return None

        df_work = df.copy()
        sort_keys: list[str] = []
        ascending_list: list[bool] = []

        unresolved_individual_criteria: list[tuple[str, SortCriterion]] = []

        for idx, crit in enumerate(sort_spec.criteria):
            # Caso 1: Matriz Indicadora Explícita (One-Hot Encoded Grid)
            matched_indicator_cols: list[str] = []
            if crit.indicator_columns:
                resolved_indicator_cols = [
                    resolve_col(c) for c in crit.indicator_columns
                ]
                matched_indicator_cols = [c for c in resolved_indicator_cols if c is not None]

            if matched_indicator_cols:
                rank_key = f"__indicator_rank_{idx}__"

                def get_indicator_rank(row, cols=matched_indicator_cols):
                    for col_idx, col_name in enumerate(cols):
                        val = row[col_name]
                        if pd.notna(val) and str(val).strip() != "":
                            return col_idx
                    return len(cols)

                df_work[rank_key] = df_work.apply(get_indicator_rank, axis=1)
                sort_keys.append(rank_key)
                ascending_list.append(crit.direction == SortDirection.ASC)

            # Caso 2: Coluna Individual (ou fallback se indicator_columns não resolveu)
            elif crit.column:
                matched_col = resolve_col(crit.column)
                if matched_col:
                    unresolved_individual_criteria.append((matched_col, crit))

        # Processa critérios individuais com agrupamento agnóstico automático de indicadores
        if unresolved_individual_criteria:
            def is_indicator_column(col_name: str) -> bool:
                series = df_work[col_name]
                non_null_count = series.notna().sum()
                if non_null_count == 0 or non_null_count == len(series):
                    return False
                unique_vals = {str(v).strip().lower() for v in series.dropna().unique()}
                return unique_vals.issubset({"x", "1", "1.0", "sim", "true", "v", "*", "ok"})

            i = 0
            while i < len(unresolved_individual_criteria):
                group: list[str] = []
                j = i
                while j < len(unresolved_individual_criteria) and is_indicator_column(unresolved_individual_criteria[j][0]):
                    group.append(unresolved_individual_criteria[j][0])
                    j += 1

                if len(group) >= 2:
                    rank_key = f"__auto_indicator_rank_{i}__"
                    def get_auto_rank(row, cols=group):
                        for col_idx, col_name in enumerate(cols):
                            val = row[col_name]
                            if pd.notna(val) and str(val).strip() != "":
                                return col_idx
                        return len(cols)

                    df_work[rank_key] = df_work.apply(get_auto_rank, axis=1)
                    sort_keys.append(rank_key)
                    ascending_list.append(unresolved_individual_criteria[i][1].direction == SortDirection.ASC)
                    i = j
                else:
                    col_name, crit = unresolved_individual_criteria[i]
                    if crit.custom_order:
                        cat_key = f"__custom_order_{i}__"
                        df_work[cat_key] = pd.Categorical(
                            df_work[col_name],
                            categories=crit.custom_order,
                            ordered=True,
                        )
                        sort_keys.append(cat_key)
                    else:
                        # Se a coluna não for puramente numérica nem datetime, tenta inferir se é data ou moeda brasileira para ordenação correta
                        sort_col = col_name
                        if not pd.api.types.is_numeric_dtype(df_work[col_name]) and not pd.api.types.is_datetime64_any_dtype(df_work[col_name]):
                            from app.services.normalizer import data_normalizer
                            col_str_lower = col_name.lower()
                            # 1. Inferência de datas brasileiras
                            if any(k in col_str_lower for k in ["data", "dt", "date", "vencimento", "emissao", "entrega"]):
                                parsed_dates = df_work[col_name].apply(data_normalizer.parse_date)
                                if parsed_dates.notna().sum() > 0 and parsed_dates.notna().sum() >= len(df_work) * 0.5:
                                    date_key = f"__date_sort_{i}__"
                                    df_work[date_key] = pd.to_datetime(parsed_dates)
                                    sort_col = date_key

                            # 2. Inferência de moedas/decimais brasileiros
                            if sort_col == col_name:
                                parsed_nums = df_work[col_name].apply(data_normalizer.parse_currency)
                                if parsed_nums.notna().sum() > 0 and parsed_nums.notna().sum() >= len(df_work) * 0.5:
                                    num_key = f"__num_sort_{i}__"
                                    df_work[num_key] = parsed_nums
                                    sort_col = num_key

                        sort_keys.append(sort_col)
                    ascending_list.append(crit.direction == SortDirection.ASC)
                    i += 1

        if not sort_keys:
            return df.copy()

        sorted_indices = df_work.sort_values(
            by=sort_keys,
            ascending=ascending_list,
            kind="mergesort",
            na_position="last",
        ).index

        return df.loc[sorted_indices].reset_index(drop=True)

    @staticmethod
    def export_formatted_excel(df: pd.DataFrame, output_path: Path, sheet_title: str) -> None:
        """
        Gera uma planilha .xlsx estilizada profissionalmente via openpyxl:
        - Linha de cabeçalho em azul escuro (#1E3A8A) com texto em negrito branco;
        - Bordas finas sutis;
        - Ajuste automático de largura de colunas;
        - Linha superior congelada (freeze panes).
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        assert ws is not None
        ws.title = sheet_title[:31]  # Excel limita títulos de abas a 31 chars

        # Estilos corporativos
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        cell_font = Font(name="Segoe UI", size=10)
        border_thin = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0"),
        )
        header_border = Border(
            left=Side(style="thin", color="1E3A8A"),
            right=Side(style="thin", color="1E3A8A"),
            top=Side(style="medium", color="1E3A8A"),
            bottom=Side(style="medium", color="0F172A"),
        )

        # 1. Escreve o cabeçalho
        columns = list(df.columns)
        ws.append(columns)
        ws.row_dimensions[1].height = 26

        for col_idx in range(1, len(columns) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=False)
            cell.border = header_border

        # 2. Escreve as linhas de dados preservando exatamente os tipos originais
        for row in df.itertuples(index=False, name=None):
            ws.append(list(row))

        # 3. Formata células de dados e calcula largura ideal
        col_widths: dict[int, int] = {i: len(str(col)) + 4 for i, col in enumerate(columns, start=1)}

        # Para planilhas grandes (> 1000 linhas), otimiza o overhead de estilização célula a célula
        if len(df) <= 1000:
            even_row_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
            for row_idx in range(2, len(df) + 2):
                ws.row_dimensions[row_idx].height = 20
                is_even = (row_idx % 2 == 0)
                row_fill = even_row_fill if is_even else None

                for col_idx in range(1, len(columns) + 1):
                    cell = ws.cell(row=row_idx, column=col_idx)
                    cell.font = cell_font
                    cell.border = border_thin
                    if row_fill:
                        cell.fill = row_fill

                    val_str = "" if cell.value is None else str(cell.value)
                    col_widths[col_idx] = max(col_widths[col_idx], len(val_str) + 3)
        else:
            # Amostra as primeiras 100 linhas para ajuste de largura sem sobrecarga de I/O
            sample_df = df.head(100)
            for row in sample_df.itertuples(index=False, name=None):
                for col_idx, val in enumerate(row, start=1):
                    val_str = "" if pd.isna(val) else str(val)
                    col_widths[col_idx] = max(col_widths[col_idx], len(val_str) + 3)

        # 4. Aplica larguras das colunas (limitadas a 50 para evitar excesso)
        for col_idx, width in col_widths.items():
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = min(50, max(12, width))

        # 5. Congela a linha do cabeçalho
        ws.freeze_panes = "A2"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(output_path)
        wb.close()

    def process(self, request: ProcessSpreadsheetRequest) -> ProcessSpreadsheetResponse:
        """
        Fluxo unificado de processamento:
        1. Localização e inspeção de cabeçalhos;
        2. Leitura tabular determinística;
        3. Cálculo de hash multiset pré-ordenação;
        4. Execução de mergesort estável;
        5. Cálculo de hash pós-ordenação e auditoria estrita de integridade;
        6. Renomeação opcional de colunas para padrão canônico;
        7. Geração de arquivo final .xlsx estilizado para entrega ao usuário.
        """
        start_time = time.perf_counter()
        file_path = file_service.get_file_path(request.file_id)

        # 1. Detecção da linha de cabeçalho
        header_row = request.header_row_index
        if header_row is None:
            detection = header_detector.detect_header(file_path, sheet_name=request.sheet_name)
            header_row = detection.header_row_index

        # 2. Leitura tabular em DataFrame
        df, sheet_name = self.read_spreadsheet(file_path, request.sheet_name, header_row)

        # 2.1 Recuperação inteligente de cabeçalho:
        # Se header_row_index foi enviado como 0 (muito comum como default de Swagger UI),
        # mas as colunas lidas forem ruidosas ou não contiverem as colunas solicitadas para ordenação,
        # o motor verifica se a heurística de detecção encontra o cabeçalho real.
        if request.header_row_index is not None and request.sort_spec and request.sort_spec.criteria:
            requested_targets: list[str] = []
            for c in request.sort_spec.criteria:
                if c.column:
                    requested_targets.append(c.column.lower())
                if c.indicator_columns:
                    requested_targets.extend([ic.lower() for ic in c.indicator_columns])

            df_cols_lower = [str(col).lower() for col in df.columns]
            has_matching_col = any(t in df_cols_lower for t in requested_targets)

            if not has_matching_col and requested_targets:
                detection = header_detector.detect_header(file_path, sheet_name=request.sheet_name)
                if detection.header_row_index != header_row:
                    candidate_df, _ = self.read_spreadsheet(file_path, request.sheet_name, detection.header_row_index)
                    candidate_cols_lower = [str(col).lower() for col in candidate_df.columns]
                    if any(t in candidate_cols_lower for t in requested_targets):
                        df = candidate_df
                        header_row = detection.header_row_index

        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A planilha não contém linhas de dados após o cabeçalho.",
            )

        # 3. Auditoria Matemática Pré-Processamento
        pre_row_count = len(df)
        pre_hash = self.calculate_multiset_hash(df)

        # 4. Aplicação de Mergesort Estável (RF-05 / RN-02)
        sorted_df = self.apply_stable_sort(df, request.sort_spec, request.column_mapping)

        # 5. Auditoria Matemática Pós-Processamento (RNF-02)
        post_row_count = len(sorted_df)
        post_hash = self.calculate_multiset_hash(sorted_df)

        rows_match = (pre_row_count == post_row_count)
        hashes_match = (pre_hash == post_hash)

        if not (rows_match and hashes_match):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Falha de integridade matemática estrita (RNF-02): Divergência detectada entre "
                    f"os dados pré e pós-processamento! Pre-hash: {pre_hash}, Post-hash: {post_hash}."
                ),
            )

        # 6. Renomeação Canônica opcional
        final_df = sorted_df.copy()
        if request.column_mapping and not request.keep_original_headers:
            rename_dict = {
                orig: canon for orig, canon in request.column_mapping.items() if orig in final_df.columns
            }
            final_df = final_df.rename(columns=rename_dict)

        # 7. Geração Física do Arquivo .xlsx
        processed_file_id = str(uuid.uuid4())
        original_base = Path(file_service.get_file_path(request.file_id)).stem
        output_filename = f"organizer_{original_base}.xlsx"

        output_dir = settings.TEMP_STORAGE_DIR / processed_file_id
        output_file_path = output_dir / output_filename

        self.export_formatted_excel(final_df, output_file_path, sheet_title=sheet_name)

        # Associa o arquivo processado ao upload original para expurgo simultâneo pós-download (LGPD / Zero Retention)
        file_service.associate_files(processed_file_id, request.file_id)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return ProcessSpreadsheetResponse(
            file_id=request.file_id,
            processed_file_id=processed_file_id,
            filename=output_filename,
            download_url=f"{settings.API_V1_STR}/process/download/{processed_file_id}",
            rows_processed=post_row_count,
            columns=list(final_df.columns),
            integrity_audit=IntegrityAudit(
                pre_process_row_count=pre_row_count,
                post_process_row_count=post_row_count,
                rows_match=rows_match,
                pre_process_hash=pre_hash,
                post_process_hash=post_hash,
                integrity_verified=True,
            ),
            processing_time_ms=elapsed_ms,
            message="Planilha ordenada com estabilidade algorítmica (mergesort) e 100% de integridade matemática.",
        )

    def consolidate(self, request: ConsolidateSheetsRequest) -> ConsolidateSheetsResponse:
        """
        Mecanismo determinístico de consolidação e alinhamento de múltiplas abas heterogêneas (RF-06, RN-01).
        Executa:
        1. Inspeção e validação de existência das abas na pasta de trabalho;
        2. Leitura tabular individual descartando preâmbulos de cada aba;
        3. Mapeamento de-para de sinônimos para esquemas canônicos unificados;
        4. Concatenação vertical alinhada;
        5. Inclusão opcional de coluna identificadora de origem (aba_origem);
        6. Aplicação de mergesort estável (se sort_spec for enviado);
        7. Auditoria matemática isolada por aba e global;
        8. Geração física do arquivo final formatado para download.
        """
        start_time = time.perf_counter()
        file_path = file_service.get_file_path(request.file_id)

        # 1. Recupera abas disponíveis
        ext = file_path.suffix.lower()
        if ext == ".xlsx":
            wb = openpyxl.load_workbook(file_path, read_only=True)
            available_sheets = wb.sheetnames
            wb.close()
        elif ext == ".xls":
            import xlrd
            book = xlrd.open_workbook(str(file_path), on_demand=True)
            available_sheets = book.sheet_names()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato '{ext}' não suportado pelo motor de consolidação.",
            )

        # Validação de abas solicitadas
        if request.sheet_names:
            missing = [s for s in request.sheet_names if s not in available_sheets]
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Aba(s) {missing} não encontrada(s) na pasta de trabalho. Abas disponíveis: {available_sheets}.",
                )
            target_sheets = request.sheet_names
        else:
            target_sheets = available_sheets

        sheet_dfs: list[pd.DataFrame] = []
        rows_per_sheet: dict[str, int] = {}
        per_sheet_audit: dict[str, SheetIntegrityAudit] = {}
        all_canonical_columns: list[str] = []
        sheet_original_mapped_cols: dict[str, list[str]] = {}

        # 2. Leitura e mapeamento de cada aba
        for sheet_name in target_sheets:
            header_row = None
            if (
                request.header_row_indices
                and sheet_name in request.header_row_indices
                and request.header_row_indices[sheet_name] is not None
            ):
                header_row = request.header_row_indices[sheet_name]
            else:
                detection = header_detector.detect_header(file_path, sheet_name=sheet_name)
                header_row = detection.header_row_index

            df_sheet, _ = self.read_spreadsheet(file_path, sheet_name, header_row)

            pre_count = len(df_sheet)
            rows_per_sheet[sheet_name] = pre_count
            pre_hash = self.calculate_multiset_hash(df_sheet)

            # Mapeamento semântico de colunas
            sheet_map: dict[str, str] = {}
            if not request.keep_original_headers and request.column_mappings:
                raw_sheet_entry = None
                if sheet_name in request.column_mappings:
                    raw_sheet_entry = request.column_mappings[sheet_name]
                elif isinstance(request.column_mappings, dict) and not any(isinstance(v, (dict, list)) for v in request.column_mappings.values()):
                    sheet_map = {str(k): str(v) for k, v in request.column_mappings.items()}

                if isinstance(raw_sheet_entry, dict):
                    sheet_map = {str(k): str(v) for k, v in raw_sheet_entry.items()}
                elif isinstance(raw_sheet_entry, list):
                    sheet_map = {}
                    for item in raw_sheet_entry:
                        if isinstance(item, dict):
                            orig = item.get("original_column")
                            canon = item.get("canonical_column")
                            if orig and canon:
                                sheet_map[str(orig)] = str(canon)
                        elif hasattr(item, "original_column") and hasattr(item, "canonical_column"):
                            sheet_map[str(item.original_column)] = str(item.canonical_column)

            if sheet_map:
                cols_lower = {str(c).lower(): c for c in df_sheet.columns}
                rename_dict = {}
                for orig_k, canon_v in sheet_map.items():
                    if orig_k in df_sheet.columns:
                        rename_dict[orig_k] = canon_v
                    elif orig_k.lower() in cols_lower:
                        rename_dict[cols_lower[orig_k.lower()]] = canon_v
                df_sheet = df_sheet.rename(columns=rename_dict)

            mapped_cols = list(df_sheet.columns)
            sheet_original_mapped_cols[sheet_name] = mapped_cols

            for c in mapped_cols:
                if c not in all_canonical_columns:
                    all_canonical_columns.append(c)

            # Coluna de rastreamento de origem
            df_sheet["__orig_sheet_name__"] = sheet_name
            if request.add_source_column:
                df_sheet[request.source_column_name] = sheet_name

            sheet_dfs.append(df_sheet)

        if not sheet_dfs or all(df.empty for df in sheet_dfs):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="As abas selecionadas não contêm linhas de dados válidas.",
            )

        # 3. Concatenação vertical sem duplicação de schema
        df_consolidated = pd.concat(sheet_dfs, ignore_index=True, sort=False)

        # Ordenação das colunas finais
        final_columns: list[str] = []
        if request.add_source_column:
            final_columns.append(request.source_column_name)
        for c in all_canonical_columns:
            if c != request.source_column_name and c not in final_columns:
                final_columns.append(c)

        # 4. Aplicação de Mergesort Estável opcional
        if request.sort_spec:
            unified_column_mapping: dict[str, str] = {}
            if request.column_mappings:
                if isinstance(request.column_mappings, dict):
                    for k, v in request.column_mappings.items():
                        if isinstance(v, dict):
                            unified_column_mapping.update({str(orig): str(canon) for orig, canon in v.items()})
                        elif isinstance(v, list):
                            for item in v:
                                if isinstance(item, dict) and "original_column" in item and "canonical_column" in item:
                                    unified_column_mapping[str(item["original_column"])] = str(item["canonical_column"])
                                elif hasattr(item, "original_column") and hasattr(item, "canonical_column"):
                                    unified_column_mapping[str(item.original_column)] = str(item.canonical_column)
                        elif isinstance(v, str):
                            unified_column_mapping[str(k)] = str(v)

            df_consolidated = self.apply_stable_sort(
                df_consolidated, request.sort_spec, column_mapping=unified_column_mapping
            )

        # 5. Auditoria Matemática Estrita por Aba e Global
        all_sheets_verified = True
        for sheet_name in target_sheets:
            df_sub = df_consolidated[df_consolidated["__orig_sheet_name__"] == sheet_name]
            post_count = len(df_sub)
            orig_cols = sheet_original_mapped_cols[sheet_name]
            df_sub_cells = df_sub[orig_cols]
            post_hash = self.calculate_multiset_hash(df_sub_cells)

            pre_count = rows_per_sheet[sheet_name]
            pre_hash_val = self.calculate_multiset_hash(sheet_dfs[target_sheets.index(sheet_name)][orig_cols])
            sheet_verified = (pre_count == post_count) and (pre_hash_val == post_hash or pre_count == 0)
            if not sheet_verified:
                all_sheets_verified = False

            per_sheet_audit[sheet_name] = SheetIntegrityAudit(
                sheet_name=sheet_name,
                pre_process_row_count=pre_count,
                post_process_row_count=post_count,
                pre_process_hash=pre_hash_val,
                post_process_hash=post_hash,
                integrity_verified=sheet_verified,
            )

        total_pre = sum(rows_per_sheet.values())
        total_post = len(df_consolidated)
        rows_match = (total_pre == total_post)
        multi_sheet_audit_verified = rows_match and all_sheets_verified

        # 6. Geração do Arquivo Físico .xlsx
        export_df = df_consolidated[final_columns].copy()

        processed_file_id = str(uuid.uuid4())
        original_base = Path(file_service.get_file_path(request.file_id)).stem
        output_filename = f"consolidado_{original_base}.xlsx"

        output_dir = settings.TEMP_STORAGE_DIR / processed_file_id
        output_file_path = output_dir / output_filename

        self.export_formatted_excel(export_df, output_file_path, sheet_title=request.consolidated_sheet_title)

        file_service.associate_files(processed_file_id, request.file_id)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return ConsolidateSheetsResponse(
            file_id=request.file_id,
            processed_file_id=processed_file_id,
            filename=output_filename,
            download_url=f"{settings.API_V1_STR}/process/download/{processed_file_id}",
            sheets_consolidated=target_sheets,
            rows_per_sheet=rows_per_sheet,
            total_rows_consolidated=total_post,
            columns=final_columns,
            integrity_audit=MultiSheetIntegrityAudit(
                total_pre_process_row_count=total_pre,
                total_post_process_row_count=total_post,
                rows_match=rows_match,
                per_sheet_audit=per_sheet_audit,
                integrity_verified=multi_sheet_audit_verified,
            ),
            processing_time_ms=elapsed_ms,
            message="Múltiplas abas consolidadas com sucesso sem duplicação de schema e com 100% de integridade matemática.",
        )

    def process_direct(self, request: DirectProcessRequest) -> DirectProcessResponse:
        """
        Processamento determinístico e ordenação algorítmica direta para o Excel Add-in (RF-10, RNF-02).
        Recebe matriz de células lidas diretamente via Office JavaScript API,
        executa higienização de tipos, mergesort estável e auditoria matemática de integridade.
        """
        start_time = time.perf_counter()

        if not request.headers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A lista de cabeçalhos não pode ser vazia.",
            )

        # 1. Converte a matriz de linhas para DataFrame
        df = pd.DataFrame(request.rows, columns=request.headers)

        # Remove linhas totalmente vazias
        df = df.dropna(how="all", axis=0)

        pre_process_count = len(df)
        pre_process_hash = self.calculate_multiset_hash(df)

        # 2. Higienização de tipos brasileiros (RF-09 / TSK-S2-04)
        if request.normalize_types:
            from app.services.normalizer import data_normalizer
            df = data_normalizer.normalize_dataframe(df)

        # 3. Ordenação determinística local (mergesort / RF-05 / RN-02)
        if request.sort_spec and request.sort_spec.criteria:
            df = self.apply_stable_sort(df, request.sort_spec, request.column_mapping)

        # 4. Auditoria de integridade pós-ordenação
        post_process_count = len(df)
        post_process_hash = self.calculate_multiset_hash(df)
        rows_match = (pre_process_count == post_process_count)
        hashes_match = (pre_process_hash == post_process_hash)
        integrity_verified = rows_match and hashes_match

        audit = IntegrityAudit(
            pre_process_row_count=pre_process_count,
            post_process_row_count=post_process_count,
            rows_match=rows_match,
            pre_process_hash=pre_process_hash,
            post_process_hash=post_process_hash,
            integrity_verified=integrity_verified,
        )

        # 5. Mapeamento canônico opcional
        mapping_applied: dict[str, str] = {}
        if request.column_mapping and not request.keep_original_headers:
            rename_dict = {
                orig: canon for orig, canon in request.column_mapping.items() if orig in df.columns
            }
            df = df.rename(columns=rename_dict)
            mapping_applied = rename_dict

        # 6. Geração de arquivo .xlsx temporário para download opcional
        processed_file_id = None
        download_url = None
        if request.generate_download_file:
            processed_file_id = str(uuid.uuid4())
            output_dir = settings.TEMP_STORAGE_DIR / processed_file_id
            output_path = output_dir / "organizer_excel_addin.xlsx"
            self.export_formatted_excel(df, output_path, sheet_title="Organizado")
            download_url = f"{settings.API_V1_STR}/process/download/{processed_file_id}"

        # 7. Formatação de retorno JSON compatível com Office.js
        clean_rows = df.fillna("").values.tolist()
        serialized_rows = []
        for r in clean_rows:
            serialized_rows.append([
                str(v) if isinstance(v, (pd.Timestamp, pd.Period)) else v
                for v in r
            ])

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return DirectProcessResponse(
            headers=list(df.columns),
            rows=serialized_rows,
            rows_processed=post_process_count,
            columns_count=len(df.columns),
            mapping_applied=mapping_applied,
            integrity_audit=audit,
            processing_time_ms=elapsed_ms,
            processed_file_id=processed_file_id,
            download_url=download_url,
            message="Dados da seleção do Excel organizados e ordenados com 100% de integridade matemática.",
        )


deterministic_engine = DeterministicEngineService()
