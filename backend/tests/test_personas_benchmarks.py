import pytest
from app.schemas.process import ProcessSpreadsheetRequest
from app.schemas.semantic import SemanticOrchestratorRequest
from app.services.file_service import file_service
from app.services.header_detector import header_detector
from app.services.processor import deterministic_engine
from app.services.semantic_orchestrator import semantic_orchestrator


@pytest.mark.asyncio
async def test_persona_carlos_apparel_grid(tmp_path):
    """
    Homologação da Persona Carlos (Confecção & Uniformes):
    Testa planilha com preâmbulo de 3 linhas, matriz indicadora (PP a XG)
    e ordenação determinística por grade.
    """
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["CONFECÇÃO ESTRELA DO NORTE - RELATÓRIO DE CORTE"])
    ws.append(["Emissão: 20/11/2026 - Turno Tarde"])
    ws.append([])
    ws.append(["Pedido", "Cliente", "Cidade", "PP", "P", "M", "G", "GG", "XG", "Total"])
    ws.append(["#101", "Colégio Santa Maria", "Natal", "", "", "X", "", "", "", 20])
    ws.append(["#102", "Academia TopFit", "Parnamirim", "X", "", "", "", "", "", 15])
    ws.append(["#103", "Tech Solutions", "Natal", "", "", "", "X", "", "", 35])

    file_path = tmp_path / "carlos_grid.xlsx"
    wb.save(file_path)
    wb.close()

    file_id = "test_carlos_uuid"
    target_dir = file_service.temp_dir / file_id
    target_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(file_path, target_dir / "carlos_grid.xlsx")

    # 1. Detecção heurística
    detection = header_detector.detect_header(file_path)
    assert detection.header_row_index == 3

    # 2. Orquestração semântica
    sem_req = SemanticOrchestratorRequest(
        columns=detection.clean_columns,
        user_instruction="Organize por tamanho das camisetas do PP ao XG e depois cidade",
    )
    sem_res = await semantic_orchestrator.orchestrate(sem_req)
    assert sem_res.proposal.sort_spec is not None

    # 3. Processamento determinístico
    proc_req = ProcessSpreadsheetRequest(
        file_id=file_id,
        header_row_index=detection.header_row_index,
        sort_spec=sem_res.proposal.sort_spec,
    )
    proc_res = deterministic_engine.process(proc_req)
    assert proc_res.rows_processed == 3
    assert proc_res.integrity_audit.integrity_verified is True


@pytest.mark.asyncio
async def test_persona_mariana_bpo_financial(tmp_path):
    """
    Homologação da Persona Mariana (BPO Financeiro):
    Testa extrato bancário com moedas formatadas em R$, débitos e créditos
    e ordenação decrescente por valor.
    """
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["BANCO ITAÚ - EXTRATO DE CONTA CORRENTE"])
    ws.append([])
    ws.append(["Data Movimento", "Histórico Transação", "Número Doc", "Valor R$", "Saldo R$"])
    ws.append(["05/11/2026", "TED Recebida Alfa", "TED 101", "R$ 14.500,00", "R$ 28.500,00"])
    ws.append(["08/11/2026", "Pagamento GPS Previdência", "DEB 202", "-R$ 3.420,50", "R$ 25.079,50"])
    ws.append(["12/11/2026", "PIX Recebido Venda", "PIX 303", "R$ 2.890,00", "R$ 27.969,50"])

    file_path = tmp_path / "mariana_extrato.xlsx"
    wb.save(file_path)
    wb.close()

    file_id = "test_mariana_uuid"
    target_dir = file_service.temp_dir / file_id
    target_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(file_path, target_dir / "mariana_extrato.xlsx")

    detection = header_detector.detect_header(file_path)
    assert detection.header_row_index == 2

    sem_req = SemanticOrchestratorRequest(
        columns=detection.clean_columns,
        user_instruction="Ordenar por maior valor financeiro decrescente",
    )
    sem_res = await semantic_orchestrator.orchestrate(sem_req)

    proc_req = ProcessSpreadsheetRequest(
        file_id=file_id,
        header_row_index=detection.header_row_index,
        sort_spec=sem_res.proposal.sort_spec,
    )
    proc_res = deterministic_engine.process(proc_req)
    assert proc_res.rows_processed == 3
    assert proc_res.integrity_audit.integrity_verified is True


@pytest.mark.asyncio
async def test_persona_rodrigo_logistics_quotes(tmp_path):
    """
    Homologação da Persona Rodrigo (Compras & Logística):
    Testa tabela de cotação de fretes com prazos e valores e ordenação por menor custo.
    """
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["COTAÇÃO COMPARATIVA DE FRETES RODOVIÁRIOS"])
    ws.append([])
    ws.append(["Transportadora", "Rota", "Peso KG", "Prazo Dias", "Valor Frete R$"])
    ws.append(["Expresso São Miguel", "SP -> PR", 450, 3, "R$ 1.450,00"])
    ws.append(["Jamef Encomendas", "SP -> SC", 450, 2, "R$ 1.820,00"])
    ws.append(["Rápido Cometa", "SP -> SC", 450, 2, "R$ 1.390,00"])

    file_path = tmp_path / "rodrigo_fretes.xlsx"
    wb.save(file_path)
    wb.close()

    file_id = "test_rodrigo_uuid"
    target_dir = file_service.temp_dir / file_id
    target_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(file_path, target_dir / "rodrigo_fretes.xlsx")

    detection = header_detector.detect_header(file_path)
    assert detection.header_row_index == 2

    sem_req = SemanticOrchestratorRequest(
        columns=detection.clean_columns,
        user_instruction="Ordene por menor custo de frete e depois menor prazo",
    )
    sem_res = await semantic_orchestrator.orchestrate(sem_req)

    proc_req = ProcessSpreadsheetRequest(
        file_id=file_id,
        header_row_index=detection.header_row_index,
        sort_spec=sem_res.proposal.sort_spec,
    )
    proc_res = deterministic_engine.process(proc_req)
    assert proc_res.rows_processed == 3
    assert proc_res.integrity_audit.integrity_verified is True
