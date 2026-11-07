import re
from typing import Any
from app.schemas.semantic import (
    ColumnMapping,
    MappingProposal,
    NullsPosition,
    SortCriterion,
    SortDirection,
    SortSpec,
)
from app.services.llm.base import BaseLLMProvider


# Base de conhecimento de ontologia semântica para os 5 setores prioritários (DoD)
SEMANTIC_TAXONOMY: dict[str, dict[str, Any]] = {
    # 1. Financeiro
    "dt_venc": ("data_vencimento", "date", 0.96, "Sinônimo reconhecido de Data de Vencimento de título/duplicata."),
    "data_vencimento": ("data_vencimento", "date", 0.98, "Nome canônico de Data de Vencimento."),
    "venc": ("data_vencimento", "date", 0.92, "Abreviação padrão de vencimento."),
    "dt_vencto": ("data_vencimento", "date", 0.95, "Abreviação bancária de data de vencimento."),
    "val_pago": ("valor_pago", "currency", 0.97, "Abreviação comum de Valor Pago em liquidações financeiras."),
    "vlr_pago": ("valor_pago", "currency", 0.97, "Abreviação contábil de Valor Pago."),
    "valor_pago": ("valor_pago", "currency", 0.99, "Nome canônico de Valor Pago."),
    "saldo_devedor": ("saldo_devedor", "currency", 0.98, "Saldo em aberto pendente de quitação."),
    "saldo_dev": ("saldo_devedor", "currency", 0.94, "Abreviação de Saldo Devedor."),
    "num_doc": ("numero_documento", "id", 0.96, "Identificador de documento contábil/fiscal."),
    "numero_documento": ("numero_documento", "id", 0.99, "Nome canônico de identificador de documento."),
    "centro_custo": ("centro_custo", "text", 0.98, "Classificação orçamentária de Centro de Custo."),
    "cc": ("centro_custo", "text", 0.90, "Sigla corporativa frequente de Centro de Custo."),

    # 2. Vendas / Comercial
    "data_pedido": ("data_pedido", "date", 0.99, "Nome canônico de Data de Pedido de Venda."),
    "dt_pedido": ("data_pedido", "date", 0.96, "Abreviação corporativa de Data do Pedido."),
    "dt_compra": ("data_pedido", "date", 0.94, "Data de aquisição ou formalização da compra."),
    "vlr_unit": ("preco_unitario", "currency", 0.96, "Abreviação de Valor Unitário de produto."),
    "preco_unitario": ("preco_unitario", "currency", 0.99, "Nome canônico de Preço Unitário."),
    "valor_unit": ("preco_unitario", "currency", 0.95, "Sinônimo de Preço Unitário de venda."),
    "qtd_itens": ("quantidade", "integer", 0.97, "Volume ou contagem de itens encomendados."),
    "qtd": ("quantidade", "integer", 0.95, "Abreviação universal de Quantidade."),
    "qt": ("quantidade", "integer", 0.95, "Abreviação de Quantidade na confecção."),
    "quantidade": ("quantidade", "integer", 0.99, "Nome canônico de Quantidade."),
    "cod_prod": ("codigo_produto", "id", 0.97, "Identificador único ou SKU de produto."),
    "codigo_produto": ("codigo_produto", "id", 0.99, "Nome canônico de Código do Produto."),
    "sku": ("codigo_produto", "id", 0.98, "Padrão de indústria para unidade de manutenção de estoque (SKU)."),
    "cli_nome": ("nome_cliente", "text", 0.96, "Abreviação de Nome do Cliente no cadastro de vendas."),
    "nome_cliente": ("nome_cliente", "text", 0.99, "Nome canônico do cliente comprador."),
    "razao_social": ("nome_cliente", "text", 0.94, "Denominação legal de pessoa jurídica compradora."),
    "cliente": ("nome_cliente", "text", 0.98, "Designação padrão de comprador."),

    # 3. Logística / Fretes
    "prazo_entrega": ("data_entrega", "date", 0.95, "Previsão ou prazo limite de entrega da carga."),
    "data_entrega": ("data_entrega", "date", 0.99, "Nome canônico de Data de Entrega."),
    "dt_entrega": ("data_entrega", "date", 0.95, "Abreviação de Data de Entrega."),
    "tarifa_frete": ("valor_frete", "currency", 0.96, "Tarifa cobrada pela transportadora por lote."),
    "valor_frete": ("valor_frete", "currency", 0.99, "Nome canônico de Custo/Valor de Frete."),
    "vlr_frete": ("valor_frete", "currency", 0.96, "Abreviação contábil de Valor de Frete."),
    "peso_cubado": ("peso_cubado", "numeric", 0.98, "Métrica volumétrica/peso de transporte rodoviário."),
    "peso": ("peso_cubado", "numeric", 0.92, "Peso físico declarado da carga."),
    "num_cte": ("numero_cte", "id", 0.98, "Número do Conhecimento de Transporte Eletrônico."),
    "cte": ("numero_cte", "id", 0.94, "Sigla de Conhecimento de Transporte Eletrônico."),
    "destinatario": ("destinatario", "text", 0.98, "Nome ou razão do recebedor final da mercadoria."),
    "dest": ("destinatario", "text", 0.91, "Abreviação logística de Destinatário."),

    # 4. RH / Departamento Pessoal
    "data_admissao": ("data_admissao", "date", 0.99, "Nome canônico de Data de Admissão do colaborador."),
    "dt_admissao": ("data_admissao", "date", 0.96, "Abreviação de Data de Admissão."),
    "admissao": ("data_admissao", "date", 0.94, "Termo corrente para ingresso na organização."),
    "sal_base": ("salario_base", "currency", 0.97, "Abreviação de Salário Base contratual."),
    "salario_base": ("salario_base", "currency", 0.99, "Nome canônico de Salário Base."),
    "remuneracao": ("salario_base", "currency", 0.93, "Vencimento mensal do empregado."),
    "matricula": ("matricula", "id", 0.98, "Identificador funcional único do trabalhador."),
    "matr": ("matricula", "id", 0.93, "Abreviação de Matrícula funcional."),
    "cargo_func": ("cargo", "text", 0.95, "Abreviação de Cargo Funcional do colaborador."),
    "cargo": ("cargo", "text", 0.99, "Nome canônico de Cargo ou Ocupação."),
    "dep_lotacao": ("departamento", "text", 0.95, "Abreviação de Departamento ou Lotação física."),
    "departamento": ("departamento", "text", 0.99, "Nome canônico da unidade organizacional."),
    "setor": ("departamento", "text", 0.94, "Subdivisão da estrutura da empresa."),

    # 5. Confecção / Têxtil (Persona Carlos)
    "nome_do_aluno": ("nome_cliente", "text", 0.95, "Identificação nominal do cliente/aluno na confecção escolar."),
    "aluno": ("nome_cliente", "text", 0.94, "Nome do discente na grade de uniformes."),
    "nome_da_camisa": ("nome_personalizacao", "text", 0.96, "Texto ou nome personalizado a estampar na peça de vestuário."),
    "grade_tam": ("grade_tamanho", "text", 0.96, "Abreviação de Grade de Tamanhos do lote têxtil."),
    "tamanho": ("grade_tamanho", "text", 0.98, "Classificação dimensional da peça (P/M/G/GG)."),
    "tecido_comp": ("tipo_tecido", "text", 0.95, "Composição e especificação da malha têxtil."),
    "cor_lote": ("cor", "text", 0.96, "Tonalidade ou cor do lote de produção."),
    "cor": ("cor", "text", 0.98, "Cor da peça confeccionada."),
    "ref_modelo": ("referencia_modelo", "id", 0.97, "Código de referência técnica da modelagem."),
    "modelo": ("referencia_modelo", "id", 0.93, "Identificador da modelagem do corte."),
    "pp": ("grade_pp", "integer", 0.92, "Quantidade de peças no tamanho Extra Pequeno (PP)."),
    "p": ("grade_p", "integer", 0.92, "Quantidade de peças no tamanho Pequeno (P)."),
    "m": ("grade_m", "integer", 0.92, "Quantidade de peças no tamanho Médio (M)."),
    "g": ("grade_g", "integer", 0.92, "Quantidade de peças no tamanho Grande (G)."),
    "gg": ("grade_gg", "integer", 0.92, "Quantidade de peças no tamanho Extra Grande (GG)."),
    "xg": ("grade_xg", "integer", 0.92, "Quantidade de peças no tamanho Extra Grande Especial (XG)."),
    "xxg": ("grade_xxg", "integer", 0.92, "Quantidade de peças no tamanho Especial (XXG)."),
}


class MockLLMProvider(BaseLLMProvider):
    """
    Provedor determinístico de alta performance para inferência semântica e Structured Outputs.
    Usado em desenvolvimento local, suítes de teste e modo de custo zero com 100% de previsibilidade.
    """

    async def generate_mapping_proposal(
        self,
        columns: list[str],
        instruction: str | None = None,
        domain_hint: str | None = None,
    ) -> MappingProposal:
        mappings: list[ColumnMapping] = []
        domain_counts: dict[str, int] = {
            "Financeiro": 0,
            "Vendas": 0,
            "Logística": 0,
            "RH": 0,
            "Confecção": 0,
        }

        for col in columns:
            normalized_key = self._normalize_col(col)
            if normalized_key in SEMANTIC_TAXONOMY:
                canon_name, d_type, conf, reason = SEMANTIC_TAXONOMY[normalized_key]
                self._increment_domain(normalized_key, domain_counts)
            else:
                # Heurística de fallback inteligente para nomes não cadastrados
                canon_name, d_type, conf, reason = self._infer_general_column(col)

            mappings.append(
                ColumnMapping(
                    original_column=col,
                    canonical_column=canon_name,
                    detected_type=d_type,
                    confidence=conf,
                    semantic_reasoning=reason,
                )
            )

        # Determina o domínio predominante
        domain_detected = domain_hint or self._select_predominant_domain(domain_counts)

        # Interpreta comando em linguagem natural se fornecido
        sort_spec = None
        if instruction and instruction.strip():
            sort_spec = self._parse_natural_language_sort(instruction.strip(), mappings)

        # Estimativa de tokens conforme RNF-04 (< 800 tokens)
        prompt_tokens = 50 + len(" ".join(columns)) // 3 + (len(instruction or "") // 3)
        completion_tokens = 60 + (len(mappings) * 18) + (len(sort_spec.criteria) * 12 if sort_spec else 0)
        total_tokens = prompt_tokens + completion_tokens

        return MappingProposal(
            domain_detected=domain_detected,
            mappings=mappings,
            sort_spec=sort_spec,
            estimated_prompt_tokens=prompt_tokens,
            estimated_completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    @staticmethod
    def _normalize_col(col: str) -> str:
        s = col.lower().strip()
        s = re.sub(r"[áàâã]", "a", s)
        s = re.sub(r"[éê]", "e", s)
        s = re.sub(r"[í]", "i", s)
        s = re.sub(r"[óôõ]", "o", s)
        s = re.sub(r"[ú]", "u", s)
        s = re.sub(r"[ç]", "c", s)
        s = re.sub(r"[^a-z0-9]", "_", s)
        return re.sub(r"_{2,}", "_", s).strip("_")

    @staticmethod
    def _increment_domain(norm_key: str, counts: dict[str, int]) -> None:
        if any(k in norm_key for k in ["venc", "saldo", "pago", "custo", "doc"]):
            counts["Financeiro"] += 1
        elif any(k in norm_key for k in ["pedido", "compra", "unit", "prod", "sku", "cli"]):
            counts["Vendas"] += 1
        elif any(k in norm_key for k in ["entrega", "frete", "peso", "cte", "dest"]):
            counts["Logística"] += 1
        elif any(k in norm_key for k in ["admissao", "sal", "matr", "cargo", "dep"]):
            counts["RH"] += 1
        elif any(k in norm_key for k in ["aluno", "camisa", "tam", "tecido", "cor", "pp", "gg"]):
            counts["Confecção"] += 1

    @staticmethod
    def _select_predominant_domain(counts: dict[str, int]) -> str:
        max_pair = max(counts.items(), key=lambda x: x[1])
        if max_pair[1] > 0:
            return max_pair[0]
        return "Geral"

    @staticmethod
    def _infer_general_column(col: str) -> tuple[str, str, float, str]:
        s = col.lower().strip()
        clean = re.sub(r"[^a-zA-Z0-9_]", "_", s).strip("_")
        if not clean:
            clean = "coluna"

        if any(k in s for k in ["data", "dt", "date", "dia", "mes", "ano"]):
            return clean, "date", 0.85, "Inferido formato de data por radical temporal no rótulo."
        if any(k in s for k in ["valor", "preco", "preço", "custo", "total", "saldo", "tarifa", "r$"]):
            return clean, "currency", 0.85, "Inferido formato monetário por radical financeiro no rótulo."
        if any(k in s for k in ["qtd", "quantidade", "num", "numero", "cont", "itens"]):
            return clean, "integer", 0.85, "Inferido valor numérico/inteiro por termo quantitativo."
        if any(k in s for k in ["cod", "id", "cpf", "cnpj", "chave", "matricula"]):
            return clean, "id", 0.90, "Inferido identificador único cadastral."

        return clean, "text", 0.80, "Classificação genérica de texto padronizada em snake_case."

    def _parse_natural_language_sort(
        self,
        instruction: str,
        mappings: list[ColumnMapping],
    ) -> SortSpec:
        """
        Interpreta comandos textuais em português (RF-04) convertendo-os em SortCriterion.
        Exemplos suportados:
        - "ordenar por data mais recente e depois maior valor"
        - "ordene por cliente crescente e valor decrescente"
        - "organizar por data pedido e depois cliente"
        - "ordenar por tamanho de camisa" (agrupamento matricial têxtil PP -> XXG)
        """
        inst_lower = instruction.lower()
        criteria: list[SortCriterion] = []
        explanation_parts: list[str] = []

        # 1. Trata caso especial de ordenação por grade têxtil multi-coluna (Confecção)
        size_hierarchy = [
            "rn", "0", "1", "2", "3", "4", "6", "8", "10", "12", "14", "16",
            "pp", "p", "m", "g", "gg", "xg", "xxg", "xxxg", "exg", "g1", "g2", "g3", "g4"
        ]
        is_size_instruction = (
            any(term in inst_lower for term in ["tamanho", "grade", "camisa"])
            and "nome da camisa" not in inst_lower
            and "nome_da_camisa" not in inst_lower
        )

        size_mappings: list[ColumnMapping] = []
        if is_size_instruction:
            for size_key in size_hierarchy:
                for m in mappings:
                    norm_orig = self._normalize_col(m.original_column)
                    norm_canon = self._normalize_col(m.canonical_column)
                    if norm_orig == size_key or norm_canon in (f"grade_{size_key}", f"tamanho_{size_key}"):
                        if m not in size_mappings:
                            size_mappings.append(m)

        if len(size_mappings) >= 2:
            for m in size_mappings:
                criteria.append(
                    SortCriterion(
                        column=m.canonical_column,
                        direction=SortDirection.ASC,
                        nulls_position=NullsPosition.LAST,
                    )
                )
            grade_repr = " -> ".join([m.original_column for m in size_mappings])
            explanation_parts.append(
                f"grade têxtil multi-coluna ({grade_repr}) em ordem canônica com nulos ao final"
            )

        # 2. Divide por conectores comuns ("e depois", "e em seguida", ",", "e")
        clauses = re.split(r",|\be depois\b|\be em seguida\b|\be\b", inst_lower)

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue

            # Se a cláusula é referente a tamanho e já foi processada pelo bloco têxtil multi-coluna, pula
            if len(size_mappings) >= 2 and any(term in clause for term in ["tamanho", "grade", "camisa"]) and "nome" not in clause:
                continue

            # Detecta direção
            direction = SortDirection.ASC
            if any(w in clause for w in ["recente", "decrescente", "maior", "desc", "z-a"]):
                direction = SortDirection.DESC
            elif any(w in clause for w in ["antigo", "crescente", "menor", "asc", "a-z"]):
                direction = SortDirection.ASC

            # Identifica a qual coluna a cláusula se refere
            target_col = None
            for mapping in mappings:
                orig_clean = self._normalize_col(mapping.original_column)
                canon_clean = self._normalize_col(mapping.canonical_column)

                # Busca correspondência direta por tokens do nome da coluna
                tokens = orig_clean.split("_") + canon_clean.split("_")
                if any(t in clause for t in tokens if len(t) > 2):
                    target_col = mapping.canonical_column
                    break

                # Correspondência semântica por conceito/tipo
                if any(w in clause for w in ["valor", "preco", "preço", "custo", "fatura"]) and mapping.detected_type == "currency":
                    target_col = mapping.canonical_column
                    break
                if any(w in clause for w in ["data", "dia", "periodo", "prazo", "vencimento"]) and mapping.detected_type == "date":
                    target_col = mapping.canonical_column
                    break
                if any(w in clause for w in ["qtd", "quantidade", "volume", "itens"]) and mapping.detected_type == "integer":
                    target_col = mapping.canonical_column
                    break
                if any(w in clause for w in ["cliente", "aluno", "destinatario", "funcionario"]) and "nome" in canon_clean:
                    target_col = mapping.canonical_column
                    break

            if target_col and not any(c.column == target_col for c in criteria):
                criteria.append(
                    SortCriterion(
                        column=target_col,
                        direction=direction,
                        nulls_position=NullsPosition.LAST,
                    )
                )
                dir_label = "decrescente" if direction == SortDirection.DESC else "crescente"
                explanation_parts.append(f"coluna '{target_col}' em ordem {dir_label}")

        if not criteria:
            # Fallback inteligente: se houver alguma coluna de data ou identificador, usa como padrão
            for mapping in mappings:
                if mapping.detected_type == "date":
                    criteria.append(SortCriterion(column=mapping.canonical_column, direction=SortDirection.DESC))
                    explanation_parts.append(f"coluna '{mapping.canonical_column}' em ordem decrescente (mais recente)")
                    break

        explanation = (
            f"Ordenação multi-critério configurada: {'; '.join(explanation_parts)}."
            if explanation_parts
            else "Instrução textual analisada sem identificação de colunas específicas para ordenação."
        )

        return SortSpec(
            criteria=criteria,
            raw_instruction=instruction,
            explanation=explanation,
        )
