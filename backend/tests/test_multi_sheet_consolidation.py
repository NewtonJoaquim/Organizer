import io
from pathlib import Path
import openpyxl
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.file_service import file_service

client = TestClient(app)


def create_multi_sheet_workbook_bytes() -> bytes:
    """Cria uma pasta de trabalho em memória com 3 abas heterogêneas (Cenário BPO Mariana)."""
    wb = openpyxl.Workbook()

    # Aba 1: Janeiro (preâmbulo de 2 linhas + cabeçalho na linha 3)
    ws_jan = wb.active
    assert ws_jan is not None
    ws_jan.title = "Janeiro"
    ws_jan.append(["RELATÓRIO FINANCEIRO MENSAL - BPO"])
    ws_jan.append([])  # Linha vazia
    ws_jan.append(["Data Movimento", "Histórico", "Valor R$"])
    ws_jan.append(["05/01/2026", "Pagamento Fornecedor A", 1200.50])
    ws_jan.append(["10/01/2026", "Recebimento Cliente B", 3500.00])
    ws_jan.append(["15/01/2026", "Tarifa Bancária", 45.90])
    ws_jan.append(["20/01/2026", "Serviços Contábeis", 800.00])
    ws_jan.append(["28/01/2026", "Folha de Pagamento", 4500.00])

    # Aba 2: Fevereiro (preâmbulo de 1 linha + cabeçalho na linha 2)
    ws_fev = wb.create_sheet(title="Fevereiro")
    ws_fev.append(["EXTRATO CONSOLIDADO FEVEREIRO 2026"])
    ws_fev.append(["Data", "Descrição", "Valor"])
    ws_fev.append(["02/02/2026", "Aluguel Sede", 2500.00])
    ws_fev.append(["12/02/2026", "Recebimento Cliente C", 4200.00])
    ws_fev.append(["18/02/2026", "Manutenção TI", 350.00])
    ws_fev.append(["25/02/2026", "Energia Elétrica", 620.40])

    # Aba 3: Março (sem preâmbulo, cabeçalho na linha 1)
    ws_mar = wb.create_sheet(title="Março")
    ws_mar.append(["Dt_Lancamento", "Historico_Operacao", "Valor_Total"])
    ws_mar.append(["01/03/2026", "Assinatura Software ERP", 199.90])
    ws_mar.append(["14/03/2026", "Recebimento Fatura 1042", 5100.00])
    ws_mar.append(["29/03/2026", "Impostos Guia DAS", 1150.00])

    output = io.BytesIO()
    wb.save(output)
    wb.close()
    return output.getvalue()


@pytest.fixture
def uploaded_multi_sheet_file_id():
    """Faz upload da pasta de trabalho multi-abas e retorna o file_id."""
    content = create_multi_sheet_workbook_bytes()
    resp = client.post(
        "/api/upload",
        files={"file": ("extratos_bpo_trimestre.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 201
    return resp.json()["file_id"]


def test_inspect_workbook_detects_all_sheets(uploaded_multi_sheet_file_id):
    """Testa a inspeção heurística de todas as abas da pasta de trabalho completa (RF-06)."""
    resp = client.post(
        "/api/inspect/workbook",
        json={"file_id": uploaded_multi_sheet_file_id},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_sheets"] == 3
    assert data["sheet_names"] == ["Janeiro", "Fevereiro", "Março"]
    assert len(data["sheets"]) == 3

    # Validação da aba Janeiro (cabeçalho detectado na linha 2 base 0)
    jan = next(s for s in data["sheets"] if s["sheet_name"] == "Janeiro")
    assert jan["header_row_index"] == 2
    assert "Data Movimento" in jan["raw_columns"]
    assert "Valor R$" in jan["raw_columns"]
    assert jan["confidence_score"] >= 0.70

    # Validação da aba Fevereiro (cabeçalho detectado na linha 1 base 0)
    fev = next(s for s in data["sheets"] if s["sheet_name"] == "Fevereiro")
    assert fev["header_row_index"] == 1
    assert "Data" in fev["raw_columns"]
    assert "Valor" in fev["raw_columns"]

    # Validação da aba Março (cabeçalho na linha 0 base 0)
    mar = next(s for s in data["sheets"] if s["sheet_name"] == "Março")
    assert mar["header_row_index"] == 0
    assert "Dt_Lancamento" in mar["raw_columns"]
    assert "Valor_Total" in mar["raw_columns"]


def test_multi_sheet_semantic_orchestrator_aligns_synonyms():
    """Testa o mapeamento semântico unificado alinhando colunas sinônimas entre abas (RF-06, RN-01)."""
    payload = {
        "sheets": {
            "Janeiro": ["Data Movimento", "Histórico", "Valor R$"],
            "Fevereiro": ["Data", "Descrição", "Valor"],
            "Março": ["Dt_Lancamento", "Historico_Operacao", "Valor_Total"],
        },
        "user_instruction": "Junte os extratos mensais e ordene por data do mais recente ao mais antigo",
        "domain_hint": "Financeiro",
    }

    resp = client.post("/api/semantic/map-multi-sheet", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["metadata_only_compliance"] is True
    proposal = data["proposal"]
    assert proposal["domain_detected"] == "Financeiro"

    # Verifica que cada aba possui mapeamentos
    sheet_mappings = proposal["sheet_mappings"]
    assert "Janeiro" in sheet_mappings
    assert "Fevereiro" in sheet_mappings
    assert "Março" in sheet_mappings

    # Verifica lista unificada de colunas canônicas
    unified_cols = proposal["unified_canonical_columns"]
    assert len(unified_cols) > 0


def test_consolidate_all_sheets_with_canonical_mapping(uploaded_multi_sheet_file_id):
    """
    Testa a consolidação vertical alinhando colunas correspondentes sem duplicação de schema
    e com adição de coluna de identificação de aba (RF-06).
    """
    column_mappings = {
        "Janeiro": {
            "Data Movimento": "data",
            "Histórico": "descricao",
            "Valor R$": "valor",
        },
        "Fevereiro": {
            "Data": "data",
            "Descrição": "descricao",
            "Valor": "valor",
        },
        "Março": {
            "Dt_Lancamento": "data",
            "Historico_Operacao": "descricao",
            "Valor_Total": "valor",
        },
    }

    req = {
        "file_id": uploaded_multi_sheet_file_id,
        "sheet_names": None,  # Consolida todas
        "header_row_indices": None,  # Heurística automática por aba
        "column_mappings": column_mappings,
        "add_source_column": True,
        "source_column_name": "aba_origem",
        "consolidated_sheet_title": "Extrato Consolidado",
        "keep_original_headers": False,
        "sort_spec": None,
    }

    resp = client.post("/api/process/consolidate", json=req)
    assert resp.status_code == 200
    data = resp.json()

    # Validações estruturais do DoD TSK-S2-01
    assert data["sheets_consolidated"] == ["Janeiro", "Fevereiro", "Março"]
    assert data["rows_per_sheet"] == {"Janeiro": 5, "Fevereiro": 4, "Março": 3}
    assert data["total_rows_consolidated"] == 12

    # Verifica que as colunas foram alinhadas perfeitamente sem duplicação
    assert data["columns"] == ["aba_origem", "data", "descricao", "valor"]

    # Auditoria de integridade matemática estrita (RNF-02)
    audit = data["integrity_audit"]
    assert audit["total_pre_process_row_count"] == 12
    assert audit["total_post_process_row_count"] == 12
    assert audit["rows_match"] is True
    assert audit["integrity_verified"] is True

    # Auditoria detalhada por aba individual
    assert audit["per_sheet_audit"]["Janeiro"]["integrity_verified"] is True
    assert audit["per_sheet_audit"]["Fevereiro"]["integrity_verified"] is True
    assert audit["per_sheet_audit"]["Março"]["integrity_verified"] is True


def test_consolidate_with_stable_sort(uploaded_multi_sheet_file_id):
    """Testa consolidação multi-abas com ordenação estável (mergesort) sobre os registros combinados."""
    column_mappings = {
        "Data Movimento": "data",
        "Data": "data",
        "Dt_Lancamento": "data",
        "Histórico": "descricao",
        "Descrição": "descricao",
        "Historico_Operacao": "descricao",
        "Valor R$": "valor",
        "Valor": "valor",
        "Valor_Total": "valor",
    }

    sort_spec = {
        "criteria": [
            {
                "column": "valor",
                "direction": "DESC",
                "nulls_position": "last",
            }
        ],
        "raw_instruction": "Ordene do maior valor para o menor",
        "explanation": "Ordenação decrescente por valor",
    }

    req = {
        "file_id": uploaded_multi_sheet_file_id,
        "column_mappings": column_mappings,
        "add_source_column": True,
        "source_column_name": "mes_referencia",
        "sort_spec": sort_spec,
    }

    resp = client.post("/api/process/consolidate", json=req)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_rows_consolidated"] == 12
    assert data["columns"] == ["mes_referencia", "data", "descricao", "valor"]
    assert data["integrity_audit"]["integrity_verified"] is True


def test_consolidate_subset_of_sheets(uploaded_multi_sheet_file_id):
    """Testa consolidação restrita a um subconjunto de abas selecionadas."""
    req = {
        "file_id": uploaded_multi_sheet_file_id,
        "sheet_names": ["Janeiro", "Março"],  # Apenas 2 das 3 abas
        "add_source_column": True,
    }

    resp = client.post("/api/process/consolidate", json=req)
    assert resp.status_code == 200
    data = resp.json()

    assert data["sheets_consolidated"] == ["Janeiro", "Março"]
    assert data["total_rows_consolidated"] == 8  # 5 + 3


def test_consolidate_nonexistent_sheet_returns_404(uploaded_multi_sheet_file_id):
    """Testa erro 404 amigável quando o usuário solicita uma aba que não existe."""
    req = {
        "file_id": uploaded_multi_sheet_file_id,
        "sheet_names": ["Janeiro", "Abril"],
    }

    resp = client.post("/api/process/consolidate", json=req)
    assert resp.status_code == 404
    assert "Abril" in resp.json()["detail"]


def test_consolidate_without_source_column(uploaded_multi_sheet_file_id):
    """Testa consolidação quando o usuário opta por não incluir a coluna de aba de origem."""
    req = {
        "file_id": uploaded_multi_sheet_file_id,
        "add_source_column": False,
    }

    resp = client.post("/api/process/consolidate", json=req)
    assert resp.status_code == 200
    data = resp.json()

    assert "aba_origem" not in data["columns"]
    assert data["total_rows_consolidated"] == 12


def test_consolidate_download_and_zero_retention_purge():
    """Testa o fluxo completo de download da planilha consolidada e expurgo imediato LGPD (RNF-03, RN-04)."""
    # 1. Upload
    content = create_multi_sheet_workbook_bytes()
    up_resp = client.post(
        "/api/upload",
        files={"file": ("trimestre_lgpd.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert up_resp.status_code == 201
    file_id = up_resp.json()["file_id"]

    # 2. Consolidação
    cons_resp = client.post("/api/process/consolidate", json={"file_id": file_id})
    assert cons_resp.status_code == 200
    proc_id = cons_resp.json()["processed_file_id"]
    download_url = cons_resp.json()["download_url"]

    # 3. Download
    down_resp = client.get(download_url)
    assert down_resp.status_code == 200
    assert len(down_resp.content) > 0
    # Verifica que o binário retornado é um arquivo zip/excel válido
    assert down_resp.content[:2] == b"PK"

    # 4. Verifica descarte imediato pós-download (Zero Data Retention)
    assert not (file_service.temp_dir / file_id).exists()
    assert not (file_service.temp_dir / proc_id).exists()

