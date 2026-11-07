import io
from pathlib import Path
import openpyxl
from fastapi.testclient import TestClient

from app.services.header_detector import header_detector


def test_detect_header_natal_real_fixture() -> None:
    """
    Valida a identificação precisa do cabeçalho na planilha real da persona (Carlos - Confecção).
    A planilha possui 5 linhas de ruído/título institucional no topo (linhas 0 a 4),
    com o cabeçalho real na linha 5.
    """
    fixture_path = Path(__file__).parent / "fixtures" / "2_SERIE_NATAL.xlsx"
    assert fixture_path.exists(), "Planilha de teste 2_SERIE_NATAL.xlsx não encontrada."

    result = header_detector.detect_header(fixture_path)

    assert result.header_row_index == 5
    assert result.data_start_row_index == 6
    assert result.confidence_score >= 0.85
    assert result.is_fallback is False
    assert result.warning_message is None
    assert result.sheet_name == "ALFA"
    assert "ALFA" in result.available_sheets

    expected_cols = ["QT", "NOME DO ALUNO", "NOME DA CAMISA", "PP", "P", "M", "G", "GG", "XG", "XXG"]
    assert result.raw_columns == expected_cols
    assert result.clean_columns == expected_cols


def test_detect_header_clean_row_zero(tmp_path: Path) -> None:
    """Valida o funcionamento ideal onde o cabeçalho está imediatamente na primeira linha (índice 0)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Dados"
    ws.append(["ID_CLIENTE", "NOME", "CIDADE", "VALOR_FATURA", "DATA_VENDA"])
    ws.append([101, "Empresa Alpha", "Fortaleza", 1500.0, "2026-11-01"])
    ws.append([102, "Empresa Beta", "Natal", 2300.0, "2026-11-02"])

    file_path = tmp_path / "planilha_limpa.xlsx"
    wb.save(file_path)

    result = header_detector.detect_header(file_path)

    assert result.header_row_index == 0
    assert result.data_start_row_index == 1
    assert result.confidence_score >= 0.90
    assert result.is_fallback is False
    assert result.clean_columns == ["ID_CLIENTE", "NOME", "CIDADE", "VALOR_FATURA", "DATA_VENDA"]


def test_detect_header_with_preambles_and_blank_rows(tmp_path: Path) -> None:
    """Valida a detecção correta ignorando títulos, subtítulos e linhas em branco."""
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Relatório"

    # Linha 0: Título isolado
    ws.append(["ORGANIZAÇÃO XYZ LTDA - RELATÓRIO FINANCEIRO"])
    # Linha 1: Metadado
    ws.append(["Período de Apuração: Novembro/2026"])
    # Linha 2: Linha vazia
    ws.append([])
    # Linha 3: Cabeçalho real
    ws.append(["Codigo", "Descricao", "Quantidade", "Preco", "Total"])
    # Linha 4+: Dados
    ws.append(["A01", "Camisa Polo", 10, 89.90, 899.00])
    ws.append(["A02", "Calça Jeans", 5, 150.00, 750.00])

    file_path = tmp_path / "planilha_com_preambulo.xlsx"
    wb.save(file_path)

    result = header_detector.detect_header(file_path)

    assert result.header_row_index == 3
    assert result.data_start_row_index == 4
    assert result.confidence_score >= 0.85
    assert result.is_fallback is False
    assert result.clean_columns == ["Codigo", "Descricao", "Quantidade", "Preco", "Total"]


def test_detect_header_with_8_noise_rows(tmp_path: Path) -> None:
    """Valida o descarte de múltiplos ruídos (até 8 linhas de preâmbulos/metadados)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None

    for i in range(8):
        ws.append([f"Metadado de auditoria {i+1}", None, None])

    # Linha 8: Cabeçalho
    ws.append(["NUM_PEDIDO", "CLIENTE", "STATUS", "VALOR"])
    ws.append([5001, "Carlos Confecções", "Aprovado", 12000.0])
    ws.append([5002, "Mariana Contábil", "Pendente", 4500.0])

    file_path = tmp_path / "muitos_ruidos.xlsx"
    wb.save(file_path)

    result = header_detector.detect_header(file_path)

    assert result.header_row_index == 8
    assert result.data_start_row_index == 9
    assert result.clean_columns == ["NUM_PEDIDO", "CLIENTE", "STATUS", "VALOR"]


def test_detect_header_duplicate_and_empty_column_names(tmp_path: Path) -> None:
    """Valida a sanitização de colunas vazias e desambiguação de duplicadas."""
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None

    # Cabeçalho com duplicidade e coluna vazia
    ws.append(["DATA", "", "VALOR", "VALOR"])
    ws.append(["2026-11-01", "Info extra", 100.0, 200.0])

    file_path = tmp_path / "colunas_duplicadas.xlsx"
    wb.save(file_path)

    result = header_detector.detect_header(file_path)

    assert result.header_row_index == 0
    assert result.raw_columns == ["DATA", "", "VALOR", "VALOR"]
    # Deve desambiguar e preencher a coluna em branco
    assert result.clean_columns == ["DATA", "coluna_2", "VALOR", "VALOR_2"]


def test_detect_header_fallback_rn03(tmp_path: Path) -> None:
    """
    Valida a aplicação estrita da regra de negócio RN-03:
    Se a confiança for inferior a 70%, o algoritmo deve assumir a primeira linha (índice 0)
    e emitir aviso explicativo.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None

    # Planilha sem cabeçalhos textuais identificáveis (apenas números ou fragmentos isolados)
    ws.append([123.45])
    ws.append([678.90])
    ws.append([999.00])

    file_path = tmp_path / "sem_cabecalho.xlsx"
    wb.save(file_path)

    result = header_detector.detect_header(file_path)

    assert result.header_row_index == 0
    assert result.is_fallback is True
    assert result.warning_message is not None
    assert "70%" in result.warning_message


def test_inspect_headers_endpoint(client: TestClient) -> None:
    """Valida a integração completa via endpoint POST /api/inspect/headers."""
    fixture_path = Path(__file__).parent / "fixtures" / "2_SERIE_NATAL.xlsx"
    with open(fixture_path, "rb") as f:
        upload_res = client.post(
            "/api/upload",
            files={"file": ("2_SERIE_NATAL.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert upload_res.status_code == 201
    file_id = upload_res.json()["file_id"]

    # Chamada ao endpoint de inspeção
    inspect_res = client.post(
        "/api/inspect/headers",
        json={"file_id": file_id},
    )
    assert inspect_res.status_code == 200
    data = inspect_res.json()

    assert data["header_row_index"] == 5
    assert data["data_start_row_index"] == 6
    assert data["confidence_score"] >= 0.85
    assert data["is_fallback"] is False
    assert "QT" in data["clean_columns"]
    assert "NOME DO ALUNO" in data["clean_columns"]
    assert data["sheet_name"] == "ALFA"
