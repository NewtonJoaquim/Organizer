import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_process_direct_basic_sorting():
    payload = {
        "headers": ["Nome", "Data Venda", "Valor"],
        "rows": [
            ["Carlos", "20/05/2026", "R$ 350,00"],
            ["Mariana", "10/01/2026", "R$ 1.250,50"],
            ["Rodrigo", "15/03/2026", "R$ 780,20"],
        ],
        "sort_spec": {
            "criteria": [
                {
                    "column": "Valor",
                    "direction": "DESC",
                }
            ],
            "raw_instruction": "ordenar por maior valor",
            "explanation": "Ordenação decrescente por Valor",
        },
        "normalize_types": True,
        "keep_original_headers": True,
    }

    response = client.post("/api/process/direct", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["rows_processed"] == 3
    assert data["columns_count"] == 3
    assert data["integrity_audit"]["rows_match"] is True
    assert data["integrity_audit"]["integrity_verified"] is True
    assert data["integrity_audit"]["pre_process_hash"] == data["integrity_audit"]["post_process_hash"]

    # Verifica se a ordenação decrescente por Valor funcionou
    # Linha com maior valor (Mariana - 1250.5) deve ser a primeira
    assert data["rows"][0][0] == "Mariana"
    # Linha com segundo maior valor (Rodrigo - 780.2)
    assert data["rows"][1][0] == "Rodrigo"
    # Linha com menor valor (Carlos - 350.0)
    assert data["rows"][2][0] == "Carlos"


def test_process_direct_canonical_mapping_and_download():
    payload = {
        "headers": ["Cli_Nome", "Dt_Pedido", "Vlr_Total"],
        "rows": [
            ["Acme Corp", "2026-05-10", 1500.0],
            ["Beta Ltd", "2026-04-12", 2300.0],
        ],
        "column_mapping": {
            "Cli_Nome": "cliente",
            "Dt_Pedido": "data_pedido",
            "Vlr_Total": "valor_total",
        },
        "keep_original_headers": False,
        "generate_download_file": True,
    }

    response = client.post("/api/process/direct", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["headers"] == ["cliente", "data_pedido", "valor_total"]
    assert data["mapping_applied"]["Cli_Nome"] == "cliente"
    assert data["download_url"] is not None
    assert "/api/process/download/" in data["download_url"]

    # Testa download do arquivo gerado
    download_res = client.get(data["download_url"])
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_process_direct_empty_headers_validation():
    payload = {
        "headers": [],
        "rows": [["valor"]],
    }
    response = client.post("/api/process/direct", json=payload)
    assert response.status_code == 400
