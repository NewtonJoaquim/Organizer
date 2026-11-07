import io
import shutil
from collections.abc import Generator
from pathlib import Path
import openpyxl
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.file_service import file_service


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(tmp_path_factory: pytest.TempPathFactory) -> Generator[None, None, None]:
    """Configura um diretório temporário isolado e modo mock determinístico para a suíte de testes."""
    test_temp_dir = tmp_path_factory.mktemp("organizer_test_storage")
    original_temp_dir = settings.TEMP_STORAGE_DIR
    original_llm_provider = settings.LLM_PROVIDER

    settings.TEMP_STORAGE_DIR = test_temp_dir
    settings.LLM_PROVIDER = "mock"  # Garante testes instantâneos e sem consumo de tokens em testes
    file_service.temp_dir = test_temp_dir
    file_service._ensure_temp_dir()

    yield

    # Cleanup após a suíte
    shutil.rmtree(test_temp_dir, ignore_errors=True)
    settings.TEMP_STORAGE_DIR = original_temp_dir
    settings.LLM_PROVIDER = original_llm_provider


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_xlsx_bytes() -> bytes:
    """Gera uma planilha .xlsx real válida em memória para os testes."""
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Vendas"
    ws.append(["ID", "Data_Venda", "Cliente", "Valor"])
    ws.append([1, "2026-11-01", "Empresa Alpha", 1500.50])
    ws.append([2, "2026-11-02", "Empresa Beta", 2700.00])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


@pytest.fixture
def sample_xls_bytes() -> bytes:
    """Gera bytes simulando uma planilha legada .xls com a assinatura OLE2 correta."""
    ole2_header = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    return ole2_header + (b"\x00" * 512)
