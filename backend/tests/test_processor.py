import io
import time
from pathlib import Path
import openpyxl
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.schemas.process import ProcessSpreadsheetRequest
from app.schemas.semantic import (
    NullsPosition,
    SortCriterion,
    SortDirection,
    SortSpec,
)
from app.services.file_service import file_service
from app.services.processor import deterministic_engine


def test_process_real_fixture_natal(tmp_path: Path) -> None:
    """
    Valida o processamento determinístico completo na planilha real de confecção (Carlos).
    - Detecta automaticamente o cabeçalho na linha 5.
    - Ordena os alunos em ordem alfabética crescente (ASC).
    - Comprova 100% de integridade matemática (hashes idênticos).
    - Gera arquivo .xlsx estilizado e legível.
    """
    fixture_path = Path(__file__).parent / "fixtures" / "2_SERIE_NATAL.xlsx"
    assert fixture_path.exists()

    # Cria entrada temporária simulando upload
    file_id = "test-carlos-natal"
    target_dir = file_service.temp_dir / file_id
    target_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(fixture_path, target_dir / "2_SERIE_NATAL.xlsx")

    sort_spec = SortSpec(
        criteria=[
            SortCriterion(column="NOME DO ALUNO", direction=SortDirection.ASC, nulls_position=NullsPosition.LAST)
        ],
        raw_instruction="ordenar alunos em ordem alfabetica",
        explanation="Ordena por NOME DO ALUNO crescente",
    )

    request = ProcessSpreadsheetRequest(
        file_id=file_id,
        sort_spec=sort_spec,
    )

    response = deterministic_engine.process(request)

    assert response.integrity_audit.integrity_verified is True
    assert response.integrity_audit.rows_match is True
    assert response.integrity_audit.pre_process_hash == response.integrity_audit.post_process_hash
    assert response.rows_processed > 0
    assert response.filename == "organizer_2_SERIE_NATAL.xlsx"

    # Inspeciona o arquivo .xlsx gerado fisicamente
    output_path = file_service.temp_dir / response.processed_file_id / response.filename
    assert output_path.exists()

    wb = openpyxl.load_workbook(output_path, data_only=True)
    ws = wb.active
    assert ws is not None

    # Valida cabeçalho congelado e estilo
    assert ws.freeze_panes == "A2"
    first_row = [cell.value for cell in ws[1]]
    assert "NOME DO ALUNO" in first_row

    # Valida que o primeiro aluno na ordem alfabética é o correto
    aluno_idx = first_row.index("NOME DO ALUNO") + 1
    primeiro_aluno = ws.cell(row=2, column=aluno_idx).value
    segundo_aluno = ws.cell(row=3, column=aluno_idx).value
    assert str(primeiro_aluno) <= str(segundo_aluno)
    wb.close()


def test_multiset_hash_integrity_mathematical_proof() -> None:
    """
    Comprova o rigor matemático da detecção de alterações (RNF-02):
    1. O hash pré e pós-ordenação é idêntico.
    2. A modificação de um único valor em uma única célula quebra o hash.
    """
    data = {
        "id": list(range(100, 200)),
        "valor": [float(i * 15.75) for i in range(100)],
        "cliente": [f"Empresa {i % 10}" for i in range(100)],
        "status": ["Pago" if i % 2 == 0 else "Pendente" for i in range(100)],
    }
    df = pd.DataFrame(data)

    pre_hash = deterministic_engine.calculate_multiset_hash(df)

    # Ordena de forma inversa
    sorted_df = df.sort_values(by="valor", ascending=False, kind="mergesort")
    post_hash = deterministic_engine.calculate_multiset_hash(sorted_df)

    # A ordenação pura NÃO altera o hash multiset das células
    assert pre_hash == post_hash

    # Altera artificialmente 1 centavo em 1 célula
    tampered_df = sorted_df.copy()
    tampered_df.iloc[0, 1] = tampered_df.iloc[0, 1] + 0.01

    tampered_hash = deterministic_engine.calculate_multiset_hash(tampered_df)
    assert tampered_hash != pre_hash, "O hash de integridade DEVE falhar quando um valor é alterado."


def test_stable_mergesort_preserves_order_on_ties() -> None:
    """Valida a estabilidade do algoritmo mergesort em casos de empate de chaves (RN-02)."""
    # Três registros com a mesma categoria, inseridos em ordem original específica
    data = {
        "categoria": ["A", "B", "A", "B", "A"],
        "id_original": [1, 2, 3, 4, 5],
    }
    df = pd.DataFrame(data)

    sort_spec = SortSpec(
        criteria=[SortCriterion(column="categoria", direction=SortDirection.ASC)],
        explanation="Ordena por categoria",
    )

    sorted_df = deterministic_engine.apply_stable_sort(df, sort_spec, column_mapping=None)

    # Para categoria A, os IDs devem aparecer na ordem estrita [1, 3, 5]
    a_ids = sorted_df[sorted_df["categoria"] == "A"]["id_original"].tolist()
    assert a_ids == [1, 3, 5], "O mergesort deve preservar a ordem original em empates (estabilidade algorítmica)."

    # Para categoria B, os IDs devem aparecer na ordem [2, 4]
    b_ids = sorted_df[sorted_df["categoria"] == "B"]["id_original"].tolist()
    assert b_ids == [2, 4]


def test_performance_benchmark_10000_rows(tmp_path: Path) -> None:
    """
    Critério 4 do DoD: Tempo de processamento local < 2 segundos para 10.000 linhas.
    Mede a leitura, hashing pré, ordenação multi-critério mergesort, hashing pós e exportação Excel.
    """
    n_rows = 10000
    df_large = pd.DataFrame({
        "codigo": list(range(1, n_rows + 1)),
        "data_movimento": ["2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04"] * (n_rows // 4),
        "departamento": ["Vendas", "Financeiro", "Logística", "Diretoria", "TI"] * (n_rows // 5),
        "valor": [round(i * 1.37, 2) for i in range(n_rows)],
        "quantidade": [i % 50 + 1 for i in range(n_rows)],
    })

    file_id = "benchmark-10k"
    target_dir = file_service.temp_dir / file_id
    target_dir.mkdir(parents=True, exist_ok=True)
    bench_file = target_dir / "dados_10k.xlsx"
    df_large.to_excel(bench_file, index=False)

    sort_spec = SortSpec(
        criteria=[
            SortCriterion(column="departamento", direction=SortDirection.ASC),
            SortCriterion(column="valor", direction=SortDirection.DESC),
        ],
        explanation="Ordena por departamento ASC e valor DESC",
    )

    request = ProcessSpreadsheetRequest(
        file_id=file_id,
        header_row_index=0,
        sort_spec=sort_spec,
    )

    start = time.perf_counter()
    response = deterministic_engine.process(request)
    elapsed_seconds = time.perf_counter() - start

    assert response.rows_processed == 10000
    assert response.integrity_audit.integrity_verified is True
    # Validação do SLA (tempo < 2.0 segundos)
    assert elapsed_seconds < 2.0, f"Tempo de processamento ({elapsed_seconds:.3f}s) ultrapassou o teto de 2.0s."


def test_process_and_download_api_endpoints(client: TestClient) -> None:
    """Valida a integração completa via endpoints POST /api/process e GET /api/process/download."""
    fixture_path = Path(__file__).parent / "fixtures" / "2_SERIE_NATAL.xlsx"
    with open(fixture_path, "rb") as f:
        upload_res = client.post(
            "/api/upload",
            files={"file": ("2_SERIE_NATAL.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert upload_res.status_code == 201
    file_id = upload_res.json()["file_id"]

    # 1. Executa o processamento
    process_payload = {
        "file_id": file_id,
        "sort_spec": {
            "criteria": [
                {"column": "NOME DO ALUNO", "direction": "ASC", "nulls_position": "last"}
            ],
            "explanation": "Ordenação alfabética de alunos",
        },
        "column_mapping": {
            "QT": "quantidade",
            "NOME DO ALUNO": "nome_aluno",
        },
    }
    process_res = client.post("/api/process", json=process_payload)
    assert process_res.status_code == 200

    data = process_res.json()
    assert "processed_file_id" in data
    assert data["integrity_audit"]["integrity_verified"] is True
    assert "nome_aluno" in data["columns"]
    assert "quantidade" in data["columns"]

    # 2. Executa o download da planilha processada
    processed_id = data["processed_file_id"]
    download_res = client.get(f"/api/process/download/{processed_id}")
    assert download_res.status_code == 200
    assert "application/vnd.openxmlformats" in download_res.headers["content-type"]
    assert len(download_res.content) > 0

    # 3. Testa download de ID inexistente (deve retornar 404)
    download_res_404 = client.get("/api/process/download/id-inexistente")
    assert download_res_404.status_code == 404

    # 4. Segundo download do mesmo arquivo deve retornar 404 (expurgado imediatamente após o primeiro streaming)
    second_download = client.get(f"/api/process/download/{processed_id}")
    assert second_download.status_code == 404


def test_process_shirt_size_indicator_sort_matches_manual_ground_truth() -> None:
    """
    Valida a ordenação por matriz indicadora horizontal agnóstica (indicator_columns)
    comparando diretamente com o gabarito de referência organizado manualmente pelo usuário.
    Garante 100% de integridade matemática e correspondência perfeita linha por linha.
    """
    fixture_path = Path(__file__).parent / "fixtures" / "2_SERIE_NATAL.xlsx"
    ground_truth_path = Path(__file__).parent / "fixtures" / "organizado_manualmente_2_SERIE_NATAL.xlsx"
    assert fixture_path.exists()
    assert ground_truth_path.exists()

    file_id = "test-carlos-natal-size-sort"
    target_dir = file_service.temp_dir / file_id
    target_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(fixture_path, target_dir / "2_SERIE_NATAL.xlsx")

    # 1. Testa via especificação agnóstica explícita indicator_columns
    sort_spec = SortSpec(
        criteria=[
            SortCriterion(
                indicator_columns=["PP", "P", "M", "G", "GG", "XG", "XXG"],
                direction=SortDirection.ASC,
                nulls_position=NullsPosition.LAST,
            )
        ],
        raw_instruction="ordenar por tamanho de camisa",
        explanation="Ordenação agnóstica por matriz indicadora",
    )

    request = ProcessSpreadsheetRequest(
        file_id=file_id,
        sort_spec=sort_spec,
    )

    response = deterministic_engine.process(request)

    assert response.integrity_audit.integrity_verified is True
    assert response.integrity_audit.rows_match is True
    assert response.integrity_audit.pre_process_hash == response.integrity_audit.post_process_hash

    # Lê o arquivo processado gerado e compara com o gabarito manual
    output_path = file_service.temp_dir / response.processed_file_id / response.filename
    df_sorted = pd.read_excel(output_path)
    df_manual = pd.read_excel(ground_truth_path, header=1)

    sorted_qts = list(df_sorted["QT"])
    manual_qts = list(df_manual["QT"])
    assert sorted_qts == manual_qts, f"Ordem divergente:\nProcessado: {sorted_qts}\nGabarito: {manual_qts}"


def test_process_smart_header_recovery_when_row_zero_passed_by_mistake() -> None:
    """
    Valida a resiliência do motor: se o cliente/Swagger enviar header_row_index=0 por engano,
    mas a linha 0 for um preâmbulo ruidoso (CAMISAS DE LANÇAMENTO) e não contiver as colunas
    solicitadas no sort_spec, o motor deve recuperar automaticamente a linha 5 identificada
    pelo detector heurístico, ordenando os dados com perfeição.
    """
    fixture_path = Path(__file__).parent / "fixtures" / "2_SERIE_NATAL.xlsx"
    ground_truth_path = Path(__file__).parent / "fixtures" / "organizado_manualmente_2_SERIE_NATAL.xlsx"

    file_id = "test-carlos-natal-recovery"
    target_dir = file_service.temp_dir / file_id
    target_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(fixture_path, target_dir / "2_SERIE_NATAL.xlsx")

    # Envia header_row_index=0 explicitamente (como o Swagger preenche por padrão)
    request = ProcessSpreadsheetRequest(
        file_id=file_id,
        sheet_name="ALFA",
        header_row_index=0,
        sort_spec=SortSpec(
            criteria=[
                SortCriterion(
                    indicator_columns=["PP", "P", "M", "G", "GG", "XG", "XXG"],
                    direction=SortDirection.ASC,
                    nulls_position=NullsPosition.LAST,
                )
            ],
            raw_instruction="Organize por tamanho das camisetas",
            explanation="Ordenação por tamanho",
        ),
        keep_original_headers=True,
    )

    response = deterministic_engine.process(request)
    assert response.integrity_audit.integrity_verified is True

    output_path = file_service.temp_dir / response.processed_file_id / response.filename
    df_sorted = pd.read_excel(output_path)
    df_manual = pd.read_excel(ground_truth_path, header=1)

    assert list(df_sorted["QT"]) == list(df_manual["QT"])


def test_apply_stable_sort_agnostic_customer_survey_matrix() -> None:
    """Valida a ordenação agnóstica em matriz indicadora de pesquisa de satisfação (Escala Likert)."""
    df = pd.DataFrame({
        "cliente": ["Cliente 1", "Cliente 2", "Cliente 3", "Cliente 4"],
        "Péssimo": [None, None, "X", None],
        "Regular": [None, None, None, "X"],
        "Bom": ["X", None, None, None],
        "Excelente": [None, "X", None, None],
    })

    sort_spec = SortSpec(
        criteria=[
            SortCriterion(
                indicator_columns=["Péssimo", "Regular", "Bom", "Excelente"],
                direction=SortDirection.ASC,
            )
        ],
        explanation="Ordenação por escala de satisfação",
    )

    sorted_df = deterministic_engine.apply_stable_sort(df, sort_spec, column_mapping=None)
    # Esperado: Péssimo (C3), Regular (C4), Bom (C1), Excelente (C2)
    assert list(sorted_df["cliente"]) == ["Cliente 3", "Cliente 4", "Cliente 1", "Cliente 2"]


def test_apply_stable_sort_agnostic_financial_credit_rating() -> None:
    """Valida a ordenação ordinal agnóstica não-alfabética via custom_order (Rating de Crédito)."""
    df = pd.DataFrame({
        "empresa": ["Alpha S.A.", "Beta Ltda", "Gamma Corp", "Delta ME"],
        "rating": ["BBB", "AAA", "B", "AA"],
    })

    sort_spec = SortSpec(
        criteria=[
            SortCriterion(
                column="rating",
                custom_order=["AAA", "AA", "BBB", "B"],
                direction=SortDirection.ASC,
            )
        ],
        explanation="Ordenação por rating de crédito",
    )

    sorted_df = deterministic_engine.apply_stable_sort(df, sort_spec, column_mapping=None)
    assert list(sorted_df["empresa"]) == ["Beta Ltda", "Delta ME", "Alpha S.A.", "Gamma Corp"]


def test_apply_stable_sort_single_categorical_size_column() -> None:
    """Valida a ordenação de coluna única com valores ordinais arbitrários (PP, P, M, GG) via custom_order."""
    df = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "tamanho": ["GG", "PP", "M", "P"],
        "aluno": ["Carlos", "Ana", "Bia", "Daniel"],
    })

    sort_spec = SortSpec(
        criteria=[
            SortCriterion(
                column="tamanho",
                custom_order=["PP", "P", "M", "GG"],
                direction=SortDirection.ASC,
                nulls_position=NullsPosition.LAST,
            )
        ],
        explanation="Ordenação por tamanho categórico",
    )

    sorted_df = deterministic_engine.apply_stable_sort(df, sort_spec, column_mapping=None)
    assert list(sorted_df["tamanho"]) == ["PP", "P", "M", "GG"]
    assert list(sorted_df["aluno"]) == ["Ana", "Daniel", "Bia", "Carlos"]


def test_apply_stable_sort_indicator_with_dirty_values_preserves_stability() -> None:
    """Valida que marcas heterogêneas ('X', 'x', 1) em colunas indicadoras mantêm a estabilidade."""
    df = pd.DataFrame({
        "id": [10, 20, 30, 40],
        "PP": ["x", "X", None, None],
        "P": [None, None, 1, "X"],
    })

    sort_spec = SortSpec(
        criteria=[
            SortCriterion(indicator_columns=["PP", "P"], direction=SortDirection.ASC),
        ],
        explanation="Grade PP e P",
    )

    sorted_df = deterministic_engine.apply_stable_sort(df, sort_spec, column_mapping=None)
    # 10 e 20 são PP (mantêm ordem original 10, 20); 30 e 40 são P (mantêm ordem 30, 40)
    assert list(sorted_df["id"]) == [10, 20, 30, 40]
