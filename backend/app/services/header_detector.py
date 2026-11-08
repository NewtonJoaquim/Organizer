from pathlib import Path
from typing import Any
import openpyxl
import xlrd
from fastapi import HTTPException, status
from app.schemas.header import HeaderDetectionResult, WorkbookInspectionResult

MAX_INSPECTION_ROWS = 15
CONFIDENCE_THRESHOLD = 0.70  # Conforme RN-03


class HeaderDetectorService:
    """
    Serviço heurístico para identificação automatizada da linha de cabeçalho
    em planilhas corporativas heterogêneas, descartando ruídos, títulos e preâmbulos.
    Atende aos requisitos RF-02 e RN-03.
    """

    def read_sample_rows(
        self, file_path: Path, sheet_name: str | None = None, max_rows: int = MAX_INSPECTION_ROWS
    ) -> tuple[list[list[Any]], str, list[str]]:
        """
        Lê até `max_rows` linhas iniciais de uma planilha (.xlsx ou .xls).
        Retorna (linhas, nome_aba_inspecionada, todas_as_abas).
        """
        ext = file_path.suffix.lower()

        if ext == ".xlsx":
            return self._read_xlsx_sample(file_path, sheet_name, max_rows)
        elif ext == ".xls":
            return self._read_xls_sample(file_path, sheet_name, max_rows)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extensão '{ext}' não suportada para inspeção de cabeçalhos.",
            )

    def _read_xlsx_sample(
        self, file_path: Path, sheet_name: str | None, max_rows: int
    ) -> tuple[list[list[Any]], str, list[str]]:
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet_names = wb.sheetnames
        if not sheet_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A pasta de trabalho não contém abas válidas.",
            )

        target_sheet_name = sheet_name or sheet_names[0]
        if target_sheet_name not in sheet_names:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aba '{target_sheet_name}' não encontrada. Abas disponíveis: {sheet_names}",
            )

        ws = wb[target_sheet_name]
        rows: list[list[Any]] = []
        for row in ws.iter_rows(max_row=max_rows, values_only=True):
            rows.append(list(row))

        wb.close()
        return rows, target_sheet_name, sheet_names

    def _read_xls_sample(
        self, file_path: Path, sheet_name: str | None, max_rows: int
    ) -> tuple[list[list[Any]], str, list[str]]:
        try:
            book = xlrd.open_workbook(str(file_path), on_demand=True)
            sheet_names = book.sheet_names()
            if not sheet_names:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A pasta de trabalho legada não contém abas válidas.",
                )

            target_sheet_name = sheet_name or sheet_names[0]
            if target_sheet_name not in sheet_names:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Aba '{target_sheet_name}' não encontrada. Abas disponíveis: {sheet_names}",
                )

            sheet = book.sheet_by_name(target_sheet_name)
            rows: list[list[Any]] = []
            num_rows = min(max_rows, sheet.nrows)
            for row_idx in range(num_rows):
                rows.append([sheet.cell_value(row_idx, col_idx) for col_idx in range(sheet.ncols)])

            return rows, target_sheet_name, sheet_names
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erro ao processar planilha .xls: {str(e)}",
            )

    @staticmethod
    def _is_valid_header_cell(val: Any) -> bool:
        if val is None:
            return False
        s = str(val).strip()
        return len(s) > 0

    @staticmethod
    def _is_textual_column_name(val: Any) -> bool:
        """Verifica se a célula se comporta como um nome de coluna (texto e não número puro)."""
        if val is None:
            return False
        if isinstance(val, (int, float)):
            return False
        s = str(val).strip()
        if not s:
            return False
        # Se for número disfarçado de string
        try:
            float(s.replace(",", "."))
            return False
        except ValueError:
            return True

    def calculate_row_score(
        self,
        row: list[Any],
        next_row: list[Any] | None,
        max_cols: int,
    ) -> float:
        """
        Calcula a pontuação de adequação para a linha ser o cabeçalho principal.
        Retorna um valor normalizado entre 0.0 e 1.0.
        """
        non_empty = [c for c in row if self._is_valid_header_cell(c)]
        k = len(non_empty)

        if k == 0 or max_cols == 0:
            return 0.0

        # Penalidade severa para títulos isolados / preâmbulos institucionais
        # (ex: 1 célula preenchida em uma tabela de 10 colunas)
        if k == 1 and max_cols > 2:
            return 0.15

        # 1. Densidade / Largura preenchida (0.35)
        density_score = min(1.0, k / max_cols)

        # 2. Textualidade dos cabeçalhos (0.25)
        # Cabeçalhos são rótulos textuais
        textual_cells = [c for c in non_empty if self._is_textual_column_name(c)]
        textual_ratio = len(textual_cells) / k

        # 3. Unicidade das colunas (0.20)
        # Nomes de colunas válidos não se repetem na mesma tabela
        string_labels = [str(c).strip().lower() for c in non_empty]
        uniqueness_ratio = len(set(string_labels)) / k

        # Penalização por textos excessivamente longos (parágrafos/disclaimers)
        avg_len = sum(len(s) for s in string_labels) / k
        length_penalty = 1.0
        if avg_len > 45:
            length_penalty = 0.5
        elif avg_len > 80:
            length_penalty = 0.2

        # 4. Continuidade de Dados da Linha Seguinte (0.20)
        # Um cabeçalho legítimo quase sempre é sucedido por uma linha de dados povoada
        continuity_score = 0.0
        if next_row is not None:
            next_non_empty = [c for c in next_row if self._is_valid_header_cell(c)]
            next_k = len(next_non_empty)
            if next_k >= 2:
                continuity_score = min(1.0, next_k / max_cols)
                # Bonificação adicional se a linha seguinte contiver tipos mistos (dados numéricos/datas)
                has_data_types = any(isinstance(c, (int, float)) for c in next_non_empty)
                if has_data_types:
                    continuity_score = min(1.0, continuity_score + 0.15)
            elif next_k == 0:
                continuity_score = 0.0

        # Combinação ponderada
        raw_score = (
            (0.35 * density_score)
            + (0.25 * textual_ratio)
            + (0.20 * uniqueness_ratio * length_penalty)
            + (0.20 * continuity_score)
        )

        return round(min(1.0, max(0.0, raw_score)), 4)

    def detect_header(
        self,
        file_path: Path,
        sheet_name: str | None = None,
        max_rows: int = MAX_INSPECTION_ROWS,
    ) -> HeaderDetectionResult:
        """
        Executa a varredura heurística nas primeiras `max_rows` da planilha,
        selecionando a linha com maior probabilidade de ser o cabeçalho.
        Aplica a regra de negócio RN-03 em caso de confiança < 70%.
        """
        sample_rows, target_sheet, all_sheets = self.read_sample_rows(
            file_path, sheet_name=sheet_name, max_rows=max_rows
        )

        if not sample_rows:
            return HeaderDetectionResult(
                header_row_index=0,
                data_start_row_index=1,
                raw_columns=[],
                clean_columns=[],
                confidence_score=0.0,
                is_fallback=True,
                inspected_rows_count=0,
                sheet_name=target_sheet,
                available_sheets=all_sheets,
                warning_message="A planilha está vazia. Nenhuma linha encontrada.",
            )

        # Encontra a largura máxima de colunas preenchidas nas linhas iniciais
        max_cols = 0
        for r in sample_rows:
            non_empty_indices = [idx for idx, val in enumerate(r) if self._is_valid_header_cell(val)]
            if non_empty_indices:
                max_cols = max(max_cols, max(non_empty_indices) + 1)

        if max_cols == 0:
            return HeaderDetectionResult(
                header_row_index=0,
                data_start_row_index=1,
                raw_columns=[],
                clean_columns=[],
                confidence_score=0.0,
                is_fallback=True,
                inspected_rows_count=len(sample_rows),
                sheet_name=target_sheet,
                available_sheets=all_sheets,
                warning_message="Nenhum dado legível encontrado nas primeiras linhas inspecionadas.",
            )

        scores: list[float] = []
        for i, row in enumerate(sample_rows):
            next_row = sample_rows[i + 1] if (i + 1) < len(sample_rows) else None
            score = self.calculate_row_score(row[:max_cols], next_row[:max_cols] if next_row else None, max_cols)
            scores.append(score)

        # Seleciona o melhor candidato
        best_score = max(scores)
        best_index = scores.index(best_score)

        is_fallback = False
        warning = None

        # RN-03: Caso não identifique linha com confiança >= 70%, assume a primeira linha (índice 0)
        if best_score < CONFIDENCE_THRESHOLD:
            header_row_index = 0
            confidence = best_score
            is_fallback = True
            warning = (
                f"Confiança de cabeçalho ({round(best_score * 100, 1)}%) abaixo do limiar "
                f"de {int(CONFIDENCE_THRESHOLD * 100)}% (RN-03). O sistema adotou a primeira linha por padrão."
            )
        else:
            header_row_index = best_index
            confidence = best_score

        # Extração e normalização dos nomes de coluna
        selected_row = sample_rows[header_row_index][:max_cols]
        raw_columns: list[str] = []
        clean_columns: list[str] = []

        seen_names: dict[str, int] = {}
        for idx, val in enumerate(selected_row):
            raw_val = "" if val is None else str(val).strip()
            raw_columns.append(raw_val)

            # Normalização de nome canônico para o DataFrame
            clean_name = raw_val if raw_val else f"coluna_{idx + 1}"
            # Se houver duplicidade na mesma linha, desambigua (ex: valor, valor_2)
            if clean_name in seen_names:
                seen_names[clean_name] += 1
                clean_name = f"{clean_name}_{seen_names[clean_name]}"
            else:
                seen_names[clean_name] = 1

            clean_columns.append(clean_name)

        return HeaderDetectionResult(
            header_row_index=header_row_index,
            data_start_row_index=header_row_index + 1,
            raw_columns=raw_columns,
            clean_columns=clean_columns,
            confidence_score=confidence,
            is_fallback=is_fallback,
            inspected_rows_count=len(sample_rows),
            sheet_name=target_sheet,
            available_sheets=all_sheets,
            warning_message=warning,
        )

    def get_available_sheets(self, file_path: Path) -> list[str]:
        """Obtém a lista de todas as abas presentes na pasta de trabalho (.xlsx ou .xls)."""
        ext = file_path.suffix.lower()
        if ext == ".xlsx":
            wb = openpyxl.load_workbook(file_path, read_only=True)
            sheet_names = list(wb.sheetnames)
            wb.close()
            return sheet_names
        elif ext == ".xls":
            book = xlrd.open_workbook(str(file_path), on_demand=True)
            return list(book.sheet_names())
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extensão '{ext}' não suportada para leitura de abas.",
            )

    def inspect_workbook(self, file_path: Path, file_id: str) -> WorkbookInspectionResult:
        """
        Inspeciona heurísticamente todas as abas da pasta de trabalho informada (RF-06).
        Retorna o resultado de detecção de cabeçalho para cada aba individualmente.
        """
        all_sheets = self.get_available_sheets(file_path)
        if not all_sheets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A pasta de trabalho não contém abas válidas.",
            )

        results: list[HeaderDetectionResult] = []
        for sheet_name in all_sheets:
            detection = self.detect_header(file_path, sheet_name=sheet_name)
            results.append(detection)

        return WorkbookInspectionResult(
            file_id=file_id,
            total_sheets=len(all_sheets),
            sheet_names=all_sheets,
            sheets=results,
        )


header_detector = HeaderDetectorService()
