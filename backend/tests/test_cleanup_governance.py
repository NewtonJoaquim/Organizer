import io
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.services.file_service import file_service


def test_post_download_immediate_cleanup_zero_data_retention(client: TestClient) -> None:
    """
    Critério 1 do DoD: Arquivo de upload e arquivo de saída descartados logo após o encerramento do download pelo cliente.
    Garante conformidade estrita com Zero Data Retention (RNF-03 e RN-04).
    """
    fixture_path = Path(__file__).parent / "fixtures" / "2_SERIE_NATAL.xlsx"
    assert fixture_path.exists()

    # 1. Realiza upload de planilha
    with open(fixture_path, "rb") as f:
        upload_res = client.post(
            "/api/upload",
            files={"file": ("2_SERIE_NATAL.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert upload_res.status_code == 201
    file_id = upload_res.json()["file_id"]

    upload_dir = settings.TEMP_STORAGE_DIR / file_id
    assert upload_dir.exists(), "O diretório do upload deve existir antes do download."

    # 2. Executa processamento determinístico
    process_payload = {
        "file_id": file_id,
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
            "raw_instruction": "ordenar por tamanho de camisa",
            "explanation": "Ordenação por tamanho",
        },
    }
    proc_res = client.post("/api/process", json=process_payload)
    assert proc_res.status_code == 200
    proc_data = proc_res.json()
    processed_file_id = proc_data["processed_file_id"]

    proc_dir = settings.TEMP_STORAGE_DIR / processed_file_id
    assert proc_dir.exists(), "O diretório do arquivo processado deve existir antes do download."

    # 3. Executa o download da planilha
    dl_res = client.get(f"/api/process/download/{processed_file_id}")
    assert dl_res.status_code == 200
    assert len(dl_res.content) > 0

    # 4. Auditoria pós-download: ambos os diretórios temporários DEVEM ter sido destruídos imediatamente
    assert not proc_dir.exists(), f"Diretório processado '{proc_dir}' não foi excluído após o download."
    assert not upload_dir.exists(), f"Diretório de upload '{upload_dir}' não foi excluído após o download."


def test_periodic_cleanup_purges_expired_files_ttl() -> None:
    """
    Critério 2 do DoD: Rotina de limpeza de arquivos com tempo de vida superior a 15 minutos (TTL).
    Simula diretórios com tempos de modificação distintos e valida o expurgo exclusivo dos expirados.
    """
    test_expired_dir = settings.TEMP_STORAGE_DIR / "simulated-expired-dir"
    test_recent_dir = settings.TEMP_STORAGE_DIR / "simulated-recent-dir"

    test_expired_dir.mkdir(parents=True, exist_ok=True)
    test_recent_dir.mkdir(parents=True, exist_ok=True)

    dummy_expired = test_expired_dir / "antigo.xlsx"
    dummy_expired.write_text("dummy")

    dummy_recent = test_recent_dir / "recente.xlsx"
    dummy_recent.write_text("dummy")

    # Modifica o mtime do diretório expirado para 20 minutos atrás (TTL é 15 minutos)
    twenty_mins_ago = time.time() - (20 * 60)
    import os
    os.utime(test_expired_dir, (twenty_mins_ago, twenty_mins_ago))

    # Executa a purga com TTL de 15 minutos
    purged = file_service.purge_expired_files(ttl_minutes=15)
    assert purged >= 1

    # Verifica que o diretório expirado foi expurgado e o recente foi preservado
    assert not test_expired_dir.exists(), "Diretório expirado deveria ter sido removido."
    assert test_recent_dir.exists(), "Diretório recente não deveria ter sido removido."

    # Limpeza manual do diretório recente de teste
    file_service.cleanup_file("simulated-recent-dir")


def test_explicit_cleanup_endpoint(client: TestClient) -> None:
    """Valida o expurgo manual de arquivos de upload via DELETE /api/upload/{file_id}."""
    fixture_path = Path(__file__).parent / "fixtures" / "2_SERIE_NATAL.xlsx"
    with open(fixture_path, "rb") as f:
        res = client.post(
            "/api/upload",
            files={"file": ("2_SERIE_NATAL.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    file_id = res.json()["file_id"]
    target_dir = settings.TEMP_STORAGE_DIR / file_id
    assert target_dir.exists()

    # Executa descarte manual
    del_res = client.delete(f"/api/upload/{file_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True
    assert not target_dir.exists()


def test_audit_storage_compliance_endpoint(client: TestClient) -> None:
    """
    Critério 3 do DoD: Auditoria registrando conformidade e verificação de arquivos em disco.
    """
    res = client.get("/api/process/audit/storage")
    assert res.status_code == 200
    data = res.json()
    assert "active_temp_directories" in data
    assert "zero_retention_compliant" in data
    assert data["ttl_minutes"] == 15
