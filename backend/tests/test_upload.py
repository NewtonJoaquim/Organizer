import io
from fastapi.testclient import TestClient
from app.core.config import settings
from app.services.file_service import file_service


def test_health_check(client: TestClient) -> None:
    """Valida o endpoint de healthcheck /api/health."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "organizer-backend"


def test_upload_valid_xlsx(client: TestClient, sample_xlsx_bytes: bytes) -> None:
    """Valida o upload de uma planilha .xlsx válida (RF-01)."""
    files = {
        "file": ("vendas_novembro.xlsx", io.BytesIO(sample_xlsx_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    }
    response = client.post("/api/upload", files=files)
    assert response.status_code == 201

    data = response.json()
    assert "file_id" in data
    assert data["original_filename"] == "vendas_novembro.xlsx"
    assert data["sanitized_filename"] == "vendas_novembro.xlsx"
    assert data["extension"] == ".xlsx"
    assert data["size_bytes"] == len(sample_xlsx_bytes)
    assert data["size_bytes"] > 0

    # Verifica se o arquivo foi realmente persistido no diretório temporário
    file_path = file_service.get_file_path(data["file_id"])
    assert file_path.exists()
    assert file_path.stat().st_size == len(sample_xlsx_bytes)


def test_upload_valid_xls(client: TestClient, sample_xls_bytes: bytes) -> None:
    """Valida o upload de uma planilha legada .xls válida (RF-01)."""
    files = {
        "file": ("relatorio_antigo.xls", io.BytesIO(sample_xls_bytes), "application/vnd.ms-excel")
    }
    response = client.post("/api/upload", files=files)
    assert response.status_code == 201

    data = response.json()
    assert data["extension"] == ".xls"
    assert data["size_bytes"] == len(sample_xls_bytes)


def test_upload_file_size_exceeds_limit(client: TestClient) -> None:
    """Valida a rejeição com HTTP 413 quando o arquivo excede 20 MB (RF-01)."""
    # Cria payload com header de ZIP (.xlsx) mas com tamanho superior a 20 MB (ex: 20 MB + 1 KB)
    header = b"PK\x03\x04"
    exceeded_size = settings.MAX_UPLOAD_SIZE_BYTES + 1024
    fake_large_payload = header + (b"\x00" * (exceeded_size - len(header)))

    files = {
        "file": ("arquivo_pesado.xlsx", io.BytesIO(fake_large_payload), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    }
    response = client.post("/api/upload", files=files)
    assert response.status_code == 413
    assert "limite máximo permitido" in response.json()["detail"]


def test_upload_invalid_extension(client: TestClient) -> None:
    """Valida a rejeição com HTTP 400 para extensões não permitidas (ex: .csv, .py, .exe)."""
    for bad_name in ["dados.csv", "script.py", "malware.exe", "documento.pdf"]:
        files = {
            "file": (bad_name, io.BytesIO(b"conteudo qualquer"), "text/plain")
        }
        response = client.post("/api/upload", files=files)
        assert response.status_code == 400
        assert "não suportado" in response.json()["detail"]


def test_upload_path_traversal_sanitization(client: TestClient, sample_xlsx_bytes: bytes) -> None:
    """Valida a sanitização contra ataques de Path Traversal no nome do arquivo."""
    malicious_names = [
        "../../../../etc/passwd.xlsx",
        "..\\..\\windows\\system32.xlsx",
        "nested/sub/folder/hack.xlsx",
    ]
    for bad_name in malicious_names:
        files = {
            "file": (bad_name, io.BytesIO(sample_xlsx_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        response = client.post("/api/upload", files=files)
        assert response.status_code == 201
        data = response.json()

        # O nome sanitizado não pode conter barras ou dois pontos
        assert "/" not in data["sanitized_filename"]
        assert "\\" not in data["sanitized_filename"]
        assert ".." not in data["sanitized_filename"]

        # O arquivo deve residir estritamente dentro da pasta temporária do file_id
        saved_file = file_service.get_file_path(data["file_id"])
        assert saved_file.exists()
        assert saved_file.parent.name == data["file_id"]


def test_upload_corrupt_magic_bytes(client: TestClient) -> None:
    """Valida que um arquivo com extensão .xlsx mas sem header ZIP é rejeitado com HTTP 400."""
    fake_content = b"Este eh um arquivo de texto fingindo ser xlsx"
    files = {
        "file": ("falso.xlsx", io.BytesIO(fake_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    }
    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    assert "assinatura binária não corresponde" in response.json()["detail"]


def test_upload_empty_file(client: TestClient) -> None:
    """Valida a rejeição de arquivos com 0 bytes."""
    files = {
        "file": ("vazio.xlsx", io.BytesIO(b""), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    }
    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    assert "vazio" in response.json()["detail"]


def test_cleanup_file_success_and_not_found(client: TestClient, sample_xlsx_bytes: bytes) -> None:
    """Valida o endpoint de descarte imediato DELETE /api/upload/{file_id} (Zero Retention)."""
    # 1. Faz upload
    files = {
        "file": ("descarte_teste.xlsx", io.BytesIO(sample_xlsx_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    }
    upload_res = client.post("/api/upload", files=files)
    assert upload_res.status_code == 201
    file_id = upload_res.json()["file_id"]

    # 2. Executa descarte
    delete_res = client.delete(f"/api/upload/{file_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["deleted"] is True

    # 3. Tenta descartar novamente (deve retornar 404)
    delete_res_404 = client.delete(f"/api/upload/{file_id}")
    assert delete_res_404.status_code == 404
