import pytest
from fastapi.testclient import TestClient

from app.schemas.semantic import (
    SemanticOrchestratorRequest,
    SortDirection,
)
from app.services.semantic_orchestrator import semantic_orchestrator


@pytest.mark.asyncio
async def test_semantic_mapping_sector_financeiro() -> None:
    """Valida mapeamento semântico no domínio Financeiro com acurácia >= 90% (DoD)."""
    columns = ["Dt_Venc", "Val_Pago", "Saldo_Devedor", "Num_Doc", "Centro_Custo"]
    request = SemanticOrchestratorRequest(columns=columns)

    response = await semantic_orchestrator.orchestrate(request)
    proposal = response.proposal

    assert proposal.domain_detected == "Financeiro"
    assert response.metadata_only_compliance is True
    assert proposal.total_tokens < 800

    col_map = {m.original_column: m for m in proposal.mappings}
    assert col_map["Dt_Venc"].canonical_column == "data_vencimento"
    assert col_map["Dt_Venc"].detected_type == "date"
    assert col_map["Dt_Venc"].confidence >= 0.90

    assert col_map["Val_Pago"].canonical_column == "valor_pago"
    assert col_map["Val_Pago"].detected_type == "currency"
    assert col_map["Val_Pago"].confidence >= 0.90

    assert col_map["Saldo_Devedor"].canonical_column == "saldo_devedor"
    assert col_map["Saldo_Devedor"].detected_type == "currency"

    assert col_map["Num_Doc"].canonical_column == "numero_documento"
    assert col_map["Num_Doc"].detected_type == "id"

    assert col_map["Centro_Custo"].canonical_column == "centro_custo"
    assert col_map["Centro_Custo"].detected_type == "text"


@pytest.mark.asyncio
async def test_semantic_mapping_sector_vendas() -> None:
    """Valida mapeamento semântico no domínio de Vendas/Comércio com acurácia >= 90% (DoD)."""
    columns = ["Data_Pedido", "Vlr_Unit", "Qtd_Itens", "Cod_Prod", "Cli_Nome"]
    request = SemanticOrchestratorRequest(columns=columns)

    response = await semantic_orchestrator.orchestrate(request)
    proposal = response.proposal

    assert proposal.domain_detected == "Vendas"
    assert proposal.total_tokens < 800

    col_map = {m.original_column: m for m in proposal.mappings}
    assert col_map["Data_Pedido"].canonical_column == "data_pedido"
    assert col_map["Data_Pedido"].detected_type == "date"

    assert col_map["Vlr_Unit"].canonical_column == "preco_unitario"
    assert col_map["Vlr_Unit"].detected_type == "currency"

    assert col_map["Qtd_Itens"].canonical_column == "quantidade"
    assert col_map["Qtd_Itens"].detected_type == "integer"

    assert col_map["Cod_Prod"].canonical_column == "codigo_produto"
    assert col_map["Cod_Prod"].detected_type == "id"

    assert col_map["Cli_Nome"].canonical_column == "nome_cliente"
    assert col_map["Cli_Nome"].detected_type == "text"


@pytest.mark.asyncio
async def test_semantic_mapping_sector_logistica() -> None:
    """Valida mapeamento semântico no domínio Logística/Fretes com acurácia >= 90% (DoD)."""
    columns = ["Prazo_Entrega", "Tarifa_Frete", "Peso_Cubado", "Num_CTe", "Destinatario"]
    request = SemanticOrchestratorRequest(columns=columns)

    response = await semantic_orchestrator.orchestrate(request)
    proposal = response.proposal

    assert proposal.domain_detected == "Logística"
    assert proposal.total_tokens < 800

    col_map = {m.original_column: m for m in proposal.mappings}
    assert col_map["Prazo_Entrega"].canonical_column == "data_entrega"
    assert col_map["Tarifa_Frete"].canonical_column == "valor_frete"
    assert col_map["Peso_Cubado"].canonical_column == "peso_cubado"
    assert col_map["Num_CTe"].canonical_column == "numero_cte"
    assert col_map["Destinatario"].canonical_column == "destinatario"


@pytest.mark.asyncio
async def test_semantic_mapping_sector_rh() -> None:
    """Valida mapeamento semântico no domínio de RH/Pessoal com acurácia >= 90% (DoD)."""
    columns = ["Data_Admissao", "Sal_Base", "Matricula", "Cargo_Func", "Dep_Lotacao"]
    request = SemanticOrchestratorRequest(columns=columns)

    response = await semantic_orchestrator.orchestrate(request)
    proposal = response.proposal

    assert proposal.domain_detected == "RH"
    assert proposal.total_tokens < 800

    col_map = {m.original_column: m for m in proposal.mappings}
    assert col_map["Data_Admissao"].canonical_column == "data_admissao"
    assert col_map["Sal_Base"].canonical_column == "salario_base"
    assert col_map["Matricula"].canonical_column == "matricula"
    assert col_map["Cargo_Func"].canonical_column == "cargo"
    assert col_map["Dep_Lotacao"].canonical_column == "departamento"


@pytest.mark.asyncio
async def test_semantic_mapping_sector_confeccao_carlos() -> None:
    """Valida mapeamento semântico no domínio de Confecção da Persona Carlos (DoD)."""
    columns = ["QT", "NOME DO ALUNO", "NOME DA CAMISA", "PP", "Grade_Tam", "Tecido_Comp", "Cor_Lote"]
    request = SemanticOrchestratorRequest(columns=columns)

    response = await semantic_orchestrator.orchestrate(request)
    proposal = response.proposal

    assert proposal.domain_detected == "Confecção"
    assert proposal.total_tokens < 800

    col_map = {m.original_column: m for m in proposal.mappings}
    assert col_map["QT"].canonical_column == "quantidade"
    assert col_map["NOME DO ALUNO"].canonical_column == "nome_cliente"
    assert col_map["NOME DA CAMISA"].canonical_column == "nome_personalizacao"
    assert col_map["PP"].canonical_column == "grade_pp"
    assert col_map["Grade_Tam"].canonical_column == "grade_tamanho"
    assert col_map["Tecido_Comp"].canonical_column == "tipo_tecido"
    assert col_map["Cor_Lote"].canonical_column == "cor"


@pytest.mark.asyncio
async def test_natural_language_parser_sort_spec() -> None:
    """Valida o parser de comandos em linguagem natural (RF-04) convertendo em SortSpec."""
    columns = ["Data_Pedido", "Vlr_Unit", "Cli_Nome"]
    instruction = "ordenar por data mais recente e depois maior valor"
    request = SemanticOrchestratorRequest(columns=columns, user_instruction=instruction)

    response = await semantic_orchestrator.orchestrate(request)
    proposal = response.proposal

    assert proposal.sort_spec is not None
    assert len(proposal.sort_spec.criteria) >= 2

    # Primeiro critério: Data decrescente (mais recente)
    assert proposal.sort_spec.criteria[0].column == "data_pedido"
    assert proposal.sort_spec.criteria[0].direction == SortDirection.DESC

    # Segundo critério: Valor decrescente (maior valor)
    assert proposal.sort_spec.criteria[1].column == "preco_unitario"
    assert proposal.sort_spec.criteria[1].direction == SortDirection.DESC


@pytest.mark.asyncio
async def test_natural_language_parser_alphabetical_sort() -> None:
    """Valida o parser para ordenação alfabética crescente."""
    columns = ["Cli_Nome", "Vlr_Unit"]
    instruction = "ordene por cliente em ordem alfabetica crescente"
    request = SemanticOrchestratorRequest(columns=columns, user_instruction=instruction)

    response = await semantic_orchestrator.orchestrate(request)
    assert response.proposal.sort_spec is not None
    crit = response.proposal.sort_spec.criteria[0]
    assert crit.column == "nome_cliente"
    assert crit.direction == SortDirection.ASC


@pytest.mark.asyncio
async def test_lgpd_rejection_of_data_rows() -> None:
    """Valida que o sistema rejeita payloads com dados seralizados longos (RN-01 / LGPD)."""
    fake_data_row = "1; João da Silva; 123.456.789-00; Rua das Flores 123; Bairro Centro; Fortaleza-CE; Cartão de Crédito 4111..." * 2
    columns = ["ID", "Nome", fake_data_row]
    request = SemanticOrchestratorRequest(columns=columns)

    with pytest.raises(Exception) as exc_info:
        await semantic_orchestrator.orchestrate(request)

    assert "LGPD" in str(exc_info.value) or "RN-01" in str(exc_info.value)


def test_semantic_orchestrator_endpoint(client: TestClient) -> None:
    """Valida a integração completa via endpoint POST /api/semantic/map."""
    payload = {
        "columns": ["Dt_Venc", "Val_Pago", "Saldo_Devedor"],
        "user_instruction": "organizar por data vencimento mais recente",
    }
    response = client.post("/api/semantic/map", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["metadata_only_compliance"] is True
    assert "proposal" in data
    assert data["proposal"]["domain_detected"] == "Financeiro"
    assert len(data["proposal"]["mappings"]) == 3
    assert data["proposal"]["total_tokens"] < 800
    assert data["processing_time_ms"] > 0
