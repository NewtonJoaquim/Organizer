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
    IntegrityAudit,
    ProcessSpreadsheetRequest,
    ProcessSpreadsheetResponse,
)
from app.schemas.semantic import SortDirection, SortSpec
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
        Preserva a ordem relativa de registros em caso de empate.
        """
        if not sort_spec or not sort_spec.criteria:
            return df.copy()

        # Mapeamento reverso para encontrar a coluna no DataFrame caso a instrução
        # use nomes canônicos e o DataFrame ainda use nomes originais
        reverse_mapping = {}
        if column_mapping:
            reverse_mapping = {canon.lower(): orig for orig, canon in column_mapping.items()}

        sort_cols: list[str] = []
        ascending_list: list[bool] = []
        na_pos_list: list[str] = []

        df_cols_lower = {col.lower(): col for col in df.columns}

        for crit in sort_spec.criteria:
            crit_target = crit.column.lower()
            matched_col = None

            # 1. Correspondência direta pelo nome exato no DataFrame
            if crit_target in df_cols_lower:
                matched_col = df_cols_lower[crit_target]
            # 2. Correspondência via mapeamento canônico reverso
            elif crit_target in reverse_mapping and reverse_mapping[crit_target].lower() in df_cols_lower:
                matched_col = df_cols_lower[reverse_mapping[crit_target].lower()]
            # 3. Correspondência parcial / radical
            else:
                for col_lower, actual_col in df_cols_lower.items():
                    if crit_target in col_lower or col_lower in crit_target:
                        matched_col = actual_col
                        break

            if matched_col and matched_col not in sort_cols:
                sort_cols.append(matched_col)
                ascending_list.append(crit.direction == SortDirection.ASC)
                na_pos_list.append(crit.nulls_position.value)

        if not sort_cols:
            return df.copy()

        # Mergesort em Pandas é estrito, estável e executa em O(N log N)
        # na_position em sort_values aceita um valor escalar para o conjunto
        na_pos = na_pos_list[0] if na_pos_list else "last"
        sorted_df = df.sort_values(
            by=sort_cols,
            ascending=ascending_list,
            kind="mergesort",
            na_position=na_pos,
        )

        return sorted_df

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

        for row_idx in range(2, len(df) + 2):
            ws.row_dimensions[row_idx].height = 20
            # Efeito zebrado sutil em linhas pares
            is_even = (row_idx % 2 == 0)
            row_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid") if is_even else None

            for col_idx in range(1, len(columns) + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.font = cell_font
                cell.border = border_thin
                if row_fill:
                    cell.fill = row_fill

                val_str = "" if cell.value is None else str(cell.value)
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


deterministic_engine = DeterministicEngineService()
