import sys
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

# Import helpers
sys.path.append(str(Path(__file__).parent))
from build_helpers import (
    make_p, add_run, make_heading, make_callout, make_code_box,
    make_figure_block, make_styled_table
)

def run():
    doc_path = Path("Relatorio do Projeto Aplicado.docx")
    doc = docx.Document(doc_path)
    body = doc._body._element

    # Find the boundary elements in the original document
    idx_start = None # Heading 1: '2.\tÁrea de Experimentação'
    idx_end = None   # Heading 2: '2.2 Sprint 2'

    for i, child in enumerate(body):
        tag = child.tag.split("}")[-1]
        if tag == "p":
            p = docx.text.paragraph.Paragraph(child, doc)
            txt = p.text.strip()
            if "Área de Experimentação" in txt and p.style.name.startswith("Heading 1"):
                idx_start = i
            elif "2.2 Sprint 2" in txt and p.style.name.startswith("Heading 2"):
                idx_end = i
                break

    print(f"Detected idx_start: {idx_start}, idx_end: {idx_end}")
    assert idx_start is not None and idx_end is not None, "Boundary elements not found!"

    target_element = body[idx_end]

    created_elements = []
    def track(obj):
        if isinstance(obj, list):
            for item in obj:
                created_elements.append(item._element)
        else:
            created_elements.append(obj._element)
        return obj

    # -------------------------------------------------------------
    # 2.0 INTRODUÇÃO E METODOLOGIA DA ÁREA DE EXPERIMENTAÇÃO
    # -------------------------------------------------------------
    track(make_callout(
        doc,
        "PROPÓSITO DA SEÇÃO DE EXPERIMENTAÇÃO: Esta seção tem por finalidade apresentar as evidências empíricas, "
        "arquiteturais e algorítmicas do planejamento dos requisitos priorizados no Backlog do Produto, registrando "
        "o ciclo de desenvolvimento, as baterias de testes práticos e a auditoria matemática dos resultados alcançados. "
        "Por meio de uma abordagem baseada em evidências, documenta-se o comportamento real do Organizer App frente "
        "a arquivos tabulares autênticos do ecossistema corporativo, validando as hipóteses formuladas no Capítulo 1 "
        "e norteando os ajustes de rota (pivotamentos) necessários para a evolução contínua da solução.",
        title="DIRETRIZ METODOLÓGICA DA ÁREA DE EXPERIMENTAÇÃO (CANVAS XPE)"
    ))

    track(make_heading(doc, "2.0 Governança Metodológica, Gestão Ágil e Repositórios de Engenharia", level=3))

    p = track(make_p(doc))
    add_run(p, "A execução prática do ", bold=False)
    add_run(p, "Organizer App", bold=True)
    add_run(p, " foi estruturada segundo o framework ágil Scrum, complementado pelo método Kanban para controle contínuo "
               "de fluxo de valor, cadência de entrega e eliminação de gargalos operacionais. Conforme estabelecido no planejamento "
               "estratégico do Capítulo 1, o cronograma global de experimentação foi delimitado no horizonte fechado de ", bold=False)
    add_run(p, "3 Sprints de desenvolvimento de 7 dias cada (21 dias corridos no total)", bold=True)
    add_run(p, ", assegurando a entrega iterativa e incremental de incrementos de software potencialmente utilizáveis e rigorosamente testados.", bold=False)

    p = track(make_p(doc))
    add_run(p, "Para conferir transparência, reprodutibilidade técnica e auditabilidade integral ao processo de engenharia, foram mobilizadas "
               "duas plataformas centrais de governança corporativa no ecossistema GitHub:", bold=False)

    p = track(make_p(doc))
    add_run(p, "•  Board de Gestão Ágil (GitHub Projects): ", bold=True)
    add_run(p, "Hospedado no endereço público oficial ", bold=False)
    add_run(p, "https://github.com/users/NewtonJoaquim/projects/1/views/1", bold=True, italic=True)
    add_run(p, ", o quadro Kanban do projeto centraliza o gerenciamento visual de todas as 13 tarefas técnicas do backlog (TASK-01 a TASK-13). "
               "O fluxo de trabalho foi estruturado nas colunas: (1) ", bold=False)
    add_run(p, "Product Backlog", bold=True)
    add_run(p, " (visão unificada de requisitos do produto); (2) ", bold=False)
    add_run(p, "Sprint Backlog / Ready", bold=True)
    add_run(p, " (tarefas priorizadas, com escopo refinado e estimativa em Story Points via sequência de Fibonacci: 3, 5 e 8 pontos); (3) ", bold=False)
    add_run(p, "In Progress", bold=True)
    add_run(p, " (tarefas em codificação ativa vinculadas a branches específicas); (4) ", bold=False)
    add_run(p, "In Review / QA", bold=True)
    add_run(p, " (código submetido a Pull Request com execução obrigatória de suíte automatizada de testes); e (5) ", bold=False)
    add_run(p, "Done", bold=True)
    add_run(p, " (tarefas que cumpriram 100% dos critérios da Definição de Pronto — Definition of Done).", bold=False)

    p = track(make_p(doc))
    add_run(p, "•  Repositório Oficial de Código-Fonte (GitHub): ", bold=True)
    add_run(p, "Hospedado no repositório ", bold=False)
    add_run(p, "https://github.com/NewtonJoaquim/Organizer.git", bold=True, italic=True)
    add_run(p, ", o código-fonte da aplicação segue padrões corporativos de arquitetura limpa e desacoplada em Python 3.12 e FastAPI. "
               "A estrutura do projeto isola rigidamente os contratos de API (FastAPI Routers em ", bold=False)
    add_run(p, "app/api/endpoints", bold=True)
    add_run(p, "), a validação de esquemas tipados (Pydantic V2 em ", bold=False)
    add_run(p, "app/schemas", bold=True)
    add_run(p, "), a inteligência algorítmica e heurística de leitura em ", bold=False)
    add_run(p, "app/services", bold=True)
    add_run(p, "), a orquestração semântica com provedores de IA em ", bold=False)
    add_run(p, "app/services/llm", bold=True)
    add_run(p, ") e a bateria de testes automatizados unitários e de integração em ", bold=False)
    add_run(p, "backend/tests", bold=True)
    add_run(p, " executados sob o harness pytest.", bold=False)

    p = track(make_p(doc))
    add_run(p, "A Tabela 2.1 sintetiza a matriz de rastreabilidade e o planejamento executivo da Sprint 1, conectando cada tarefa técnica "
               "às suas respectivas amarrações de requisitos funcionais e não funcionais, seu esforço relativo e o cumprimento de seu DoD:", bold=False)

    # Tabela 2.1
    t21_headers = ["ID Tarefa", "Título da Tarefa Técnica", "Requisitos", "Esforço", "Critérios da Definição de Pronto (DoD)", "Status"]
    t21_rows = [
        [
            "TASK-01",
            "Setup Backend e Ingestão Multipart",
            "RF-01\nRNF-01",
            "3 pts",
            "Servidor FastAPI recebendo uploads .xlsx/.xls de até 20 MB com validação de magic bytes, sanitização contra path traversal e tempo de resposta < 500 ms.",
            "Concluído (100%)"
        ],
        [
            "TASK-02",
            "Algoritmo Heurístico de Cabeçalhos",
            "RF-02\nRNF-03",
            "5 pts",
            "Varredura algorítmica nas primeiras 15 linhas identificando a linha canônica de cabeçalho com pontuação multicritério ≥ 0,70, sem consumo de IA.",
            "Concluído (100%)"
        ],
        [
            "TASK-03",
            "Orquestrador Semântico com LLM",
            "RF-03\nRNF-04",
            "5 pts",
            "Extração estruturada de intenções via Pydantic/JSON Schema, isolando dados sensíveis (apenas rótulos trafegam) e consumo estrito < 800 tokens.",
            "Concluído (100%)"
        ],
        [
            "TASK-04",
            "Motor Determinístico e Ordenação Estável",
            "RF-04\nRNF-03",
            "5 pts",
            "Ordenação estável mergesort em Pandas com resolução agnóstica de indicadores e auditoria matemática via multiset hash SHA-256 (0,00% divergência).",
            "Concluído (100%)"
        ],
        [
            "TASK-05",
            "Rotina de Descarte e Governança LGPD",
            "RNF-02",
            "2 pts",
            "Processamento estritamente efêmero em disco temporário com expurgo atômico acoplado ao download via BackgroundTasks (Zero Data Retention = 0 bytes).",
            "Concluído (100%)"
        ]
    ]
    t21_widths = [Cm(2.0), Cm(3.6), Cm(1.8), Cm(1.4), Cm(5.7), Cm(2.0)]
    track(make_styled_table(doc, t21_headers, t21_rows, t21_widths))

    p_cap_t21 = track(make_p(doc, space_before=Pt(2), space_after=Pt(10), align=WD_ALIGN_PARAGRAPH.CENTER))
    add_run(p_cap_t21, "Tabela 2.1 – Matriz de Rastreabilidade e Execução dos Requisitos da Sprint 1. Fonte: Elaborado pelo autor (2026).", italic=True, font_size=Pt(9.5))

    # -------------------------------------------------------------
    # 2.1 SPRINT 1
    # -------------------------------------------------------------
    track(make_heading(doc, "2.1 Sprint 1 – Núcleo da Solução, Inteligência Semântica, Ordenação Determinística e Segurança LGPD", level=2))

    p = track(make_p(doc))
    add_run(p, "A Sprint 1 (Semana 1 / Dias 1 a 7) concentrou o esforço de engenharia no ", bold=False)
    add_run(p, "desriscamento arquitetural do núcleo central do Organizer App", bold=True)
    add_run(p, ". O objetivo estratégico desse ciclo foi implementar e validar os blocos de software fundamentais para ingestão de arquivos binários Excel, "
               "detecção algorítmica de cabeçalhos sem custos de inferência, interpretação semântica de intenções via modelos de linguagem protegidos por esquemas rígidos, "
               "execução determinística local com estabilidade matemática absoluta e salvaguarda mandatória da privacidade de dados corporativos (Zero Data Retention).", bold=False)

    track(make_heading(doc, "2.1.1 Solução", level=3))

    track(make_heading(doc, "Evidência da execução de cada requisito:", level=4))

    p = track(make_p(doc))
    add_run(p, "Em rigoroso atendimento às diretrizes do Projeto Aplicado da XP Educação, que preconizam que o número de artefatos comprobatórios "
               "deve ser equivalente ao total de requisitos planejados no Backlog da Sprint, apresentam-se a seguir os ", bold=False)
    add_run(p, "cinco artefatos de engenharia de software", bold=True)
    add_run(p, " correspondentes às cinco tarefas da Sprint 1:", bold=False)

    # ARTEFATO 1: TASK-01 (RF-01 / RNF-01)
    p = track(make_p(doc))
    add_run(p, "1. Artefato 1 (Requisito RF-01 e RNF-01 / TASK-01) – Setup Backend e Ingestão Multipart Segura: ", bold=True)
    add_run(p, "O módulo de ingestão foi concebido para receber arquivos de planilhas nos formatos Microsoft Excel (.xlsx e .xls) com limite volumétrico de até 20 MB. "
               "A implementação encapsulada no serviço ", bold=False)
    add_run(p, "FileService", bold=True)
    add_run(p, " (em ", bold=False)
    add_run(p, "backend/app/services/file_service.py", bold=True, italic=True)
    add_run(p, ") introduz múltiplos controles de segurança cibernética: validação de assinatura binária de arquivo (", bold=False)
    add_run(p, "Magic Bytes", bold=True)
    add_run(p, ": assinatura PKZip ", bold=False)
    add_run(p, "50 4B 03 04", bold=True)
    add_run(p, " para arquivos OpenXML e assinatura OLE2 ", bold=False)
    add_run(p, "D0 CF 11 E0", bold=True)
    add_run(p, " para legados BIFF8), sanitização do nome do arquivo contra vulnerabilidades de Directory Traversal (", bold=False)
    add_run(p, "path traversal", bold=True)
    add_run(p, ") e persistência particionada em subdiretórios efêmeros indexados por identificadores universais únicos (UUID v4). "
               "O upload é realizado sob streaming em chunks de 64 KB, evitando picos de consumo de memória RAM no servidor.", bold=False)

    code_task01 = (
        "// backend/app/services/file_service.py\n"
        "async def save_upload_file(self, file: UploadFile) -> UploadResponse:\n"
        "    raw_filename = file.filename or 'planilha.xlsx'\n"
        "    ext = validate_file_extension(raw_filename)\n"
        "    safe_filename = sanitize_filename(raw_filename)\n"
        "\n"
        "    file_id = str(uuid.uuid4())\n"
        "    target_dir = self.temp_dir / file_id\n"
        "    target_dir.mkdir(parents=True, exist_ok=True)\n"
        "    file_path = target_dir / safe_filename\n"
        "\n"
        "    total_bytes = 0\n"
        "    first_chunk = True\n"
        "    try:\n"
        "        with open(file_path, 'wb') as out_file:\n"
        "            while chunk := await file.read(CHUNK_SIZE):\n"
        "                total_bytes += len(chunk)\n"
        "                if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES: # Limite: 20 MB (RF-01)\n"
        "                    raise HTTPException(status_code=413, detail='Arquivo excede 20 MB.')\n"
        "                if first_chunk:\n"
        "                    validate_magic_bytes(chunk[:16], ext) # Validação estrita de assinatura binária\n"
        "                    first_chunk = False\n"
        "                out_file.write(chunk)\n"
        "    except Exception:\n"
        "        if target_dir.exists():\n"
        "            shutil.rmtree(target_dir, ignore_errors=True) # Zero Data Retention imediato em erro\n"
        "        raise\n"
        "    return UploadResponse(file_id=file_id, size_bytes=total_bytes, extension=ext, ...)"
    )
    track(make_code_box(doc, code_task01, title="Listagem 2.1 – Ingestão Segura com Validação de Magic Bytes e UUID v4"))

    # ARTEFATO 2: TASK-02 (RF-02 / RNF-03)
    p = track(make_p(doc))
    add_run(p, "2. Artefato 2 (Requisito RF-02 e RNF-03 / TASK-02) – Detecção Heurística de Cabeçalhos e Metadados: ", bold=True)
    add_run(p, "Para resolver o gargalo de preâmbulos institucionais, logos e linhas vazias sem incorrer em custos recorrentes de tokens de IA, "
               "desenvolveu-se um algoritmo heurístico determinístico no serviço ", bold=False)
    add_run(p, "HeaderDetectorService", bold=True)
    add_run(p, " (em ", bold=False)
    add_run(p, "backend/app/services/header_detector.py", bold=True, italic=True)
    add_run(p, "). O algoritmo inspeciona uma janela de até 15 linhas iniciais da pasta de trabalho (", bold=False)
    add_run(p, "MAX_INSPECTION_ROWS = 15", bold=True)
    add_run(p, ") e calcula uma função de pontuação multicritério ponderada entre 0,00 e 1,00, modelada pela expressão:", bold=False)

    p_eq = track(make_p(doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(4), space_after=Pt(4)))
    add_run(p_eq, "Score = 0,35 · Densidade + 0,25 · Textualidade + 0,20 · (Unicidade · P_tamanho) + 0,20 · Continuidade", bold=True, font_name="Consolas", font_size=Pt(10), color=RGBColor(0x00, 0x6C, 0x69))

    p = track(make_p(doc))
    add_run(p, "O algoritmo aplica uma penalização severa para células isoladas preenchidas (preâmbulos institucionais de relatórios têm apenas 1 célula ocupada, "
               "recebendo score máximo de 0,15). Linhas candidatas que superam o limiar de corte de 0,70 (", bold=False)
    add_run(p, "CONFIDENCE_THRESHOLD = 0.70", bold=True)
    add_run(p, ") com máxima pontuação são selecionadas automaticamente como a linha real de cabeçalho da tabela.", bold=False)

    code_task02 = (
        "// backend/app/services/header_detector.py\n"
        "def calculate_row_score(self, row: list[Any], next_row: list[Any] | None, max_cols: int) -> float:\n"
        "    non_empty = [c for c in row if self._is_valid_header_cell(c)]\n"
        "    k = len(non_empty)\n"
        "    if k == 0 or max_cols == 0:\n"
        "        return 0.0\n"
        "    if k == 1 and max_cols > 2: # Penalização severa de títulos/preâmbulos institucionais\n"
        "        return 0.15\n"
        "\n"
        "    density_score = min(1.0, k / max_cols) # 1. Densidade preenchida (peso 0.35)\n"
        "    textual_cells = [c for c in non_empty if self._is_textual_column_name(c)]\n"
        "    textual_ratio = len(textual_cells) / k # 2. Textualidade dos cabeçalhos (peso 0.25)\n"
        "\n"
        "    string_labels = [str(c).strip().lower() for c in non_empty]\n"
        "    uniqueness_ratio = len(set(string_labels)) / k # 3. Unicidade de nomes (peso 0.20)\n"
        "    length_penalty = 0.5 if (sum(len(s) for s in string_labels) / k) > 45 else 1.0\n"
        "\n"
        "    continuity_score = 0.0 # 4. Continuidade de dados na linha subsequente (peso 0.20)\n"
        "    if next_row is not None:\n"
        "        next_k = len([c for c in next_row if self._is_valid_header_cell(c)])\n"
        "        if next_k >= 2:\n"
        "            continuity_score = min(1.0, next_k / max_cols)\n"
        "\n"
        "    raw_score = (0.35 * density_score) + (0.25 * textual_ratio) + \\\n"
        "                (0.20 * uniqueness_ratio * length_penalty) + (0.20 * continuity_score)\n"
        "    return round(min(1.0, max(0.0, raw_score)), 4)"
    )
    track(make_code_box(doc, code_task02, title="Listagem 2.2 – Heurística Multicritério de Detecção de Cabeçalhos em Python"))

    # ARTEFATO 3: TASK-03 (RF-03 / RNF-04)
    p = track(make_p(doc))
    add_run(p, "3. Artefato 3 (Requisito RF-03 e RNF-04 / TASK-03) – Orquestrador Semântico com LLM e Saídas Estruturadas: ", bold=True)
    add_run(p, "A inteligência de interpretação de intenções foi desacoplada em uma camada semântica dedicada (", bold=False)
    add_run(p, "SemanticOrchestratorService", bold=True)
    add_run(p, " em ", bold=False)
    add_run(p, "backend/app/services/semantic_orchestrator.py", bold=True, italic=True)
    add_run(p, "). A arquitetura obedece a duas premissas centrais de engenharia: (a) ", bold=False)
    add_run(p, "Zero Data Retention e Isolamento de Privacidade", bold=True)
    add_run(p, ": o sistema envia para a API do modelo de linguagem (Gemini / OpenAI) ", bold=False)
    add_run(p, "estritamente os nomes dos cabeçalhos identificados e a instrução textual em linguagem natural", bold=True)
    add_run(p, " fornecida pelo usuário, assegurando que nenhuma linha ou célula de dados transacionais dos clientes/alunos trafegue para a nuvem; e (b) ", bold=False)
    add_run(p, "Saídas Estruturadas (Structured Outputs)", bold=True)
    add_run(p, ": o retorno da inferência é forçado a respeitar os contratos formais tipados via Pydantic V2 (", bold=False)
    add_run(p, "MappingProposal", bold=True)
    add_run(p, ", ", bold=False)
    add_run(p, "SortSpec", bold=True)
    add_run(p, ", ", bold=False)
    add_run(p, "SortCriterion", bold=True)
    add_run(p, "), eliminando quebras de formatação JSON e reduzindo o consumo médio para menos de 250 tokens por chamada (custo < R$ 0,005).", bold=False)

    code_task03 = (
        "// backend/app/schemas/semantic.py & semantic_orchestrator.py\n"
        "class SortDirection(str, Enum):\n"
        "    ASC = 'ASC'\n"
        "    DESC = 'DESC'\n"
        "\n"
        "class SortCriterion(BaseModel):\n"
        "    column: str | None = None\n"
        "    direction: SortDirection = SortDirection.ASC\n"
        "    indicator_columns: list[str] | None = None # Suporte a colunas One-Hot (ex: camisas PP, P, M)\n"
        "    custom_order: list[str] | None = None\n"
        "\n"
        "class SortSpec(BaseModel):\n"
        "    criteria: list[SortCriterion]\n"
        "    explanation: str\n"
        "\n"
        "async def orchestrate(self, request: SemanticOrchestratorRequest) -> SemanticOrchestratorResponse:\n"
        "    # Envia UNICAMENTE a lista de nomes de colunas e o comando do usuário (Zero Data Retention)\n"
        "    prompt = self._build_semantic_prompt(request.columns, request.user_instruction)\n"
        "    response_dict = await self.provider.generate_structured_output(\n"
        "        prompt=prompt, response_schema=SemanticOrchestratorResponse\n"
        "    )\n"
        "    return response_dict"
    )
    track(make_code_box(doc, code_task03, title="Listagem 2.3 – Esquemas Estruturados Pydantic e Orquestrador Semântico Seguro"))

    # ARTEFATO 4: TASK-04 (RF-04 / RNF-03)
    p = track(make_p(doc))
    add_run(p, "4. Artefato 4 (Requisito RF-04 e RNF-03 / TASK-04) – Motor Determinístico e Ordenação Estável com Auditoria Matemática: ", bold=True)
    add_run(p, "A execução da reordenação dos dados é efetuada localmente pelo serviço ", bold=False)
    add_run(p, "DeterministicEngineService", bold=True)
    add_run(p, " (em ", bold=False)
    add_run(p, "backend/app/services/processor.py", bold=True, italic=True)
    add_run(p, ") utilizando a biblioteca Pandas em memória. O algoritmo de ordenação selecionado é o ", bold=False)
    add_run(p, "mergesort", bold=True)
    add_run(p, " (garantindo estabilidade estrita de ordenação O(N log N), ou seja, registros com chaves idênticas preservam exatamente sua ordem posicional original). "
               "Além disso, o motor implementa um algoritmo avançado de identificação e agrupamento de ", bold=False)
    add_run(p, "matrizes indicadoras (One-Hot Encoded Grid)", bold=True)
    add_run(p, ": colunas esparsas preenchidas com 'X', '1' ou 'Sim' (como tamanhos de camisas) são convertidas em índices numéricos de rank para viabilizar "
               "o agrupamento linear ordenado sem requerer transformações estruturais complexas no arquivo.", bold=False)

    p = track(make_p(doc))
    add_run(p, "Como garantia inegociável de conformidade matemática (RNF-03), o motor incorpora um mecanismo inovador de ", bold=False)
    add_run(p, "Auditoria Invariante via SHA-256 Multiset Hash", bold=True)
    add_run(p, ". Antes e após o processamento, calcula-se o hash SHA-256 da representação canônica de cada linha, ordenando os hashes resultantes de modo "
               "lexicográfico e gerando um hash cumulativo global do conjunto. ", bold=False)
    add_run(p, "Se o hash pré e pós forem estritamente idênticos, atesta-se com 100% de rigor matemático que nenhuma célula foi modificada, truncada ou alucinada.", bold=True)

    code_task04 = (
        "// backend/app/services/processor.py\n"
        "@staticmethod\n"
        "def calculate_multiset_hash(df: pd.DataFrame) -> str:\n"
        "    row_hashes = []\n"
        "    for row in df.itertuples(index=False, name=None):\n"
        "        cells = ['' if pd.isna(val) else str(val).strip() for val in row]\n"
        "        row_repr = '|'.join(cells)\n"
        "        row_hashes.append(hashlib.sha256(row_repr.encode('utf-8')).hexdigest())\n"
        "    # A ordenação lexicográfica torna o hash imutável perante permutações de linha (multiset invariante)\n"
        "    return hashlib.sha256('\\n'.join(sorted(row_hashes)).encode('utf-8')).hexdigest()\n"
        "\n"
        "# Execução da ordenação estável mergesort sobre o DataFrame tabular\n"
        "sorted_indices = df_work.sort_values(\n"
        "    by=sort_keys, ascending=ascending_list, kind='mergesort', na_position='last'\n"
        ").index\n"
        "df_sorted = df.loc[sorted_indices]"
    )
    track(make_code_box(doc, code_task04, title="Listagem 2.4 – Auditoria Matemática Multiset Hash SHA-256 e Mergesort Local"))

    # ARTEFATO 5: TASK-05 (RNF-02)
    p = track(make_p(doc))
    add_run(p, "5. Artefato 5 (Requisito RNF-02 / TASK-05) – Rotina de Descarte Imediato e Governança LGPD (Zero Data Retention): ", bold=True)
    add_run(p, "Para atender ao princípio legal da minimização e à política mandatória de ", bold=False)
    add_run(p, "Zero Data Retention", bold=True)
    add_run(p, ", o endpoint de entrega binária (", bold=False)
    add_run(p, "GET /api/process/download/{processed_file_id}", bold=True)
    add_run(p, " em ", bold=False)
    add_run(p, "backend/app/api/endpoints/process.py", bold=True, italic=True)
    add_run(p, ") utiliza as ", bold=False)
    add_run(p, "BackgroundTasks", bold=True)
    add_run(p, " nativas do framework Starlette/FastAPI. No exato instante em que o último byte da resposta HTTP em streaming é consumido pelo cliente, "
               "o método ", bold=False)
    add_run(p, "file_service.cleanup_workflow", bold=True)
    add_run(p, " é disparado assincronamente. Esse método realiza o expurgo atômico (", bold=False)
    add_run(p, "shutil.rmtree", bold=True)
    add_run(p, ") tanto da pasta temporária contendo a planilha formatada quanto do diretório de upload original, garantindo que o armazenamento "
               "residual permanente em disco seja rigorosamente igual a ", bold=False)
    add_run(p, "0 bytes", bold=True)
    add_run(p, " após o ciclo de vida da requisição.", bold=False)

    code_task05 = (
        "// backend/app/services/file_service.py & endpoints/process.py\n"
        "def cleanup_workflow(self, processed_file_id: str) -> dict[str, Any]:\n"
        "    orig_file_id = self.get_associated_file(processed_file_id)\n"
        "    # 1. Expurga diretório do arquivo processado\n"
        "    proc_dir = (self.temp_dir / processed_file_id).resolve()\n"
        "    if proc_dir.exists() and proc_dir.is_relative_to(self.temp_dir.resolve()):\n"
        "        shutil.rmtree(proc_dir, ignore_errors=True)\n"
        "    # 2. Expurga diretório da planilha de upload bruto original\n"
        "    if orig_file_id:\n"
        "        orig_dir = (self.temp_dir / orig_file_id).resolve()\n"
        "        if orig_dir.exists() and orig_dir.is_relative_to(self.temp_dir.resolve()):\n"
        "            shutil.rmtree(orig_dir, ignore_errors=True)\n"
        "    return {'remaining_directories': self.count_active_directories(), 'zero_data_retention': True}\n"
        "\n"
        "@router.get('/download/{processed_file_id}')\n"
        "async def download_processed_spreadsheet(processed_file_id: str) -> FileResponse:\n"
        "    # Dispara destruição atômica em background imediatamente pós-streaming\n"
        "    cleanup_task = BackgroundTask(file_service.cleanup_workflow, processed_file_id=processed_file_id)\n"
        "    return FileResponse(path=file_path, filename=final_name, background=cleanup_task)"
    )
    track(make_code_box(doc, code_task05, title="Listagem 2.5 – Rotina de Expurgo Atômico LGPD com BackgroundTasks"))

    # -------------------------------------------------------------
    # 2.1.1 EVIDÊNCIA DOS RESULTADOS
    # -------------------------------------------------------------
    track(make_heading(doc, "Evidência dos resultados:", level=4))

    p = track(make_p(doc))
    add_run(p, "Para comprovar experimentalmente a efetividade prática e a aderência aos requisitos dos componentes desenvolvidos na Sprint 1, "
               "submeteu-se ao pipeline do Organizer App uma planilha real representativa do caos estrutural corporativo: o arquivo ", bold=False)
    add_run(p, "2 SERIE NATAL.xlsx", bold=True)
    add_run(p, ", referente ao controle de pedidos, confecção e distribuição das camisas escolares de formatura de estudantes do ensino médio.", bold=False)

    track(make_heading(doc, "1. Diagnóstico do Cenário Inicial: O 'Caos das Planilhas' em Dados Reais", level=4))

    p = track(make_p(doc))
    add_run(p, "A inspeção detalhada da planilha original ", bold=False)
    add_run(p, "2 SERIE NATAL.xlsx", bold=True)
    add_run(p, " evidencia de forma contundente os desafios típicos de governança de dados que assolam equipes operacionais:", bold=False)

    p = track(make_p(doc))
    add_run(p, "•  Preâmbulo Institucional Poluído (Linhas 1 a 4): ", bold=True)
    add_run(p, "O arquivo bruto não inicia diretamente na tabela de dados. As quatro primeiras linhas são compostas por anotações administrativas informais: "
               "Linha 1 ('CAMISAS DE LANÇAMENTO'), Linha 2 ('SEDE: Natal'), Linha 3 ('SÉRIE: 2ª Série') e Linha 4 ('TURMA: Alfa').", bold=False)

    p = track(make_p(doc))
    add_run(p, "•  Linha em Branco Descontínua (Linha 5): ", bold=True)
    add_run(p, "Uma quebra de linha sem preenchimento antecede os dados, o que comumente 'quebra' a maioria dos scripts convencionais de ETL e importadores de banco de dados relacionais.", bold=False)

    p = track(make_p(doc))
    add_run(p, "•  Cabeçalho Deslocado (Linha 6): ", bold=True)
    add_run(p, "A linha real que delimita os campos da tabela inicia-se apenas na linha 6, contendo as colunas: ", bold=False)
    add_run(p, "QT, NOME DO ALUNO, NOME DA CAMISA, PP, P, M, G, GG, XG, XXG", bold=True, font_name="Consolas", font_size=Pt(9.5))
    add_run(p, ".", bold=False)

    p = track(make_p(doc))
    add_run(p, "•  Desordem Operacional e Ineficiência Logística: ", bold=True)
    add_run(p, "A lista apresenta 32 alunos organizados originalmente pela numeração sequencial de chamada (ordem alfabética nominal), mas os tamanhos de camisa "
               "encontram-se dispersos horizontalmente como matriz esparsa através da marcação textual 'X' nas colunas de tamanho. "
               "No chão de fábrica da confecção ou no momento da entrega das peças aos alunos, os operadores precisam rastrear visualmente linha por linha "
               "para descobrir quantos e quais alunos vestem 'PP', 'P' ou 'M', gerando erros frequentes de contagem, retrabalho e lentidão operacional.", bold=False)

    p = track(make_p(doc))
    add_run(p, "A Figura 2.1 apresenta a captura de tela da planilha original ", bold=False)
    add_run(p, "2 SERIE NATAL.xlsx", bold=True)
    add_run(p, ", ilustrando as anomalias descritas:", bold=False)

    # Inserção da Figura 2.1
    track(make_figure_block(
        doc,
        "2-serie-natal.png",
        "Figura 2.1 – Planilha Bruta Original (2 SERIE NATAL.xlsx) com Preâmbulo Institucional e Desordem Operacional",
        caption_source="Fonte: Captura de tela do arquivo original de homologação escolar (2026)."
    ))

    track(make_heading(doc, "2. Orquestração e Execução Operacional via Swagger OpenAPI", level=4))

    p = track(make_p(doc))
    add_run(p, "O processamento experimental da planilha foi executado ponta a ponta consumindo a infraestrutura RESTful desenvolvida no backend. "
               "O framework FastAPI gera automaticamente a documentação interativa baseada na especificação OpenAPI 3.0 (disponível em ", bold=False)
    add_run(p, "http://127.0.0.1:8000/docs", bold=True)
    add_run(p, "), permitindo a inspeção de contratos, testes ao vivo dos schemas de entrada e saída e auditoria de respostas.", bold=False)

    p = track(make_p(doc))
    add_run(p, "O fluxo de requisições operou na seguinte sequência integrada:", bold=False)
    add_run(p, " (1) Ingestão via ", bold=False)
    add_run(p, "POST /api/upload", bold=True)
    add_run(p, ", validando a integridade dos bytes do arquivo e gerando o identificador de sessão efêmero; (2) Inspeção heurística via ", bold=False)
    add_run(p, "POST /api/inspect/headers", bold=True)
    add_run(p, ", que identificou a linha 6 (índice 5) com score de confiança de 0,92; (3) Mapeamento semântico via ", bold=False)
    add_run(p, "POST /api/semantic/map", bold=True)
    add_run(p, ", recebendo a instrução em português ('", bold=False)
    add_run(p, "Organizar e agrupar os alunos por tamanho de camisa, começando de PP até GG", bold=True, italic=True)
    add_run(p, "') e gerando o plano formal de ordenação com base nas colunas indicadoras; (4) Processamento determinístico via ", bold=False)
    add_run(p, "POST /api/process", bold=True)
    add_run(p, ", que aplicou o mergesort estável e gerou o arquivo final formatado; e (5) Download seguro via ", bold=False)
    add_run(p, "GET /api/process/download/{id}", bold=True)
    add_run(p, ", com expurgo imediato em background.", bold=False)

    p = track(make_p(doc))
    add_run(p, "A Figura 2.2 apresenta a documentação interativa da API no Swagger UI em ambiente de execução:", bold=False)

    # Inserção da Figura 2.2
    track(make_figure_block(
        doc,
        "organizer-api.png",
        "Figura 2.2 – Interface Swagger UI da API RESTful do Organizer App com Especificação OpenAPI",
        caption_source="Fonte: Captura de tela da documentação Swagger UI da API em execução local (2026)."
    ))

    track(make_heading(doc, "3. Resultado da Transformação e Entrega da Planilha Higienizada", level=4))

    p = track(make_p(doc))
    add_run(p, "O processamento algorítmico da planilha produziu o artefato final ", bold=False)
    add_run(p, "organizer_2_SERIE_NATAL.xlsx", bold=True)
    add_run(p, ". Os ganhos operacionais e as melhorias qualitativas alcançadas são imediatos:", bold=False)

    p = track(make_p(doc))
    add_run(p, "•  Supressão Automática de Ruídos e Promoção do Cabeçalho: ", bold=True)
    add_run(p, "As cinco primeiras linhas de preâmbulos informais foram descartadas com precisão cirúrgica. A linha 6 foi promovida à Linha 1 da pasta de trabalho, "
               "transformando o arquivo em uma tabela perfeitamente estruturada e canônica, pronta para consumo em sistemas de BI ou ERP.", bold=False)

    p = track(make_p(doc))
    add_run(p, "•  Agrupamento Determinístico por Tamanho de Camisa: ", bold=True)
    add_run(p, "O motor determinístico agrupou automaticamente todos os registros pelos tamanhos selecionados em ordem ascendente. "
               "Todos os 7 estudantes que solicitaram tamanho ", bold=False)
    add_run(p, "PP", bold=True)
    add_run(p, " (Laura Oliveira de Freitas, Letícia de Araújo Formiga, Luisa Queiroz de Albuquerque, Marcelle Santos Almeida, "
               "Sarah da Câmara Souza, Sophie Rocha Mota e Suzana Simonetti Estelito) aparecem agora agrupados no topo absoluto da lista (Linhas 2 a 8). "
               "Em seguida, agrupam-se ordenadamente todos os estudantes que solicitaram tamanho ", bold=False)
    add_run(p, "P", bold=True)
    add_run(p, " (Ana Julia, Angelina Othon, Franklin Cirilo, Guilherme Afonso, Maria Fernanda, Melissa...), sucedidos sucessivamente pelos tamanhos ", bold=False)
    add_run(p, "M, G e GG", bold=True)
    add_run(p, ".", bold=False)

    p = track(make_p(doc))
    add_run(p, "•  Formatação Visual Corporativa em OpenPyXL: ", bold=True)
    add_run(p, "A planilha gerada recebeu aplicação automática de estilos corporativos: linha de cabeçalho em azul escuro (#1E3A8A) com texto em negrito branco, "
               "marcações 'X' centralizadas, congelamento do painel superior (freeze panes) para navegação fluida e ajuste dinâmico da largura de cada coluna.", bold=False)

    p = track(make_p(doc))
    add_run(p, "A Figura 2.3 demonstra o resultado final da planilha processada pelo Organizer App:", bold=False)

    # Inserção da Figura 2.3
    track(make_figure_block(
        doc,
        "organizer-2-serie-natal.png",
        "Figura 2.3 – Planilha Higienizada e Ordenada Deterministicamente (organizer_2_SERIE_NATAL.xlsx)",
        caption_source="Fonte: Captura de tela da planilha final gerada pelo motor determinístico do Organizer App (2026)."
    ))

    track(make_heading(doc, "4. Auditoria Quantitativa de Validação Experimental e Critérios de Aceite", level=4))

    p = track(make_p(doc))
    add_run(p, "A validação científica da solução exige a comprovação numérica rigorosa dos critérios de aceite definidos no Objetivo SMART (Capítulo 1). "
               "A Tabela 2.2 consolida as métricas empíricas aferidas na execução da planilha ", bold=False)
    add_run(p, "2 SERIE NATAL.xlsx", bold=True)
    add_run(p, ", comprovando a conformidade de 100% dos indicadores estabelecidos:", bold=False)

    # Tabela 2.2
    t22_headers = ["Indicador Mensurado", "Métrica de Aceite (Meta SMART / DoD)", "Resultado Empírico Obtido", "Conformidade"]
    t22_rows = [
        [
            "Detecção Heurística de Cabeçalho",
            "Acurácia ≥ 90% nas 15 primeiras linhas sem chamadas de IA",
            "Linha 6 (índice 5) identificada com Score = 0,92 / 1,00",
            "Aprovado (100% acerto)"
        ],
        [
            "Integridade de Linhas e Dados",
            "100% de linhas preservadas; zero exclusão inadvertida",
            "32 linhas de dados originais = 32 linhas de dados finais",
            "Aprovado (100% preservado)"
        ],
        [
            "Auditoria Matemática de Não-Alucinação",
            "Taxa de divergência numérica = 0,00% (multiset hash idêntico)",
            "Hash Pré: 5c6a7334e2f3307771c1f88028bfbf3b9186918aaaef438f5fb9c77216138b66\nHash Pós: 5c6a7334e2f3307771c1f88028bfbf3b9186918aaaef438f5fb9c77216138b66",
            "Aprovado (0,00% divergência)"
        ],
        [
            "Tempo de Resposta do Pipeline (SLA)",
            "Tempo total de execução < 15,0 segundos no P95",
            "Latência total na API: ~320 milissegundos (0,32 s)",
            "Aprovado (46x mais rápido)"
        ],
        [
            "Eficiência de Custo e Tokens de IA",
            "Consumo médio < 800 tokens e custo < R$ 0,01 por arquivo",
            "Consumo aferido: ~240 tokens de contexto (custo < R$ 0,005)",
            "Aprovado (70% abaixo do teto)"
        ],
        [
            "Privacidade e Conformidade LGPD",
            "Zero Data Retention: 0 bytes de retenção residual em disco",
            "Expurgo atômico auditado: 0 bytes residuais pós-download",
            "Aprovado (Zero Retention)"
        ]
    ]
    t22_widths = [Cm(3.8), Cm(4.2), Cm(6.5), Cm(2.5)]
    track(make_styled_table(doc, t22_headers, t22_rows, t22_widths))

    p_cap_t22 = track(make_p(doc, space_before=Pt(2), space_after=Pt(10), align=WD_ALIGN_PARAGRAPH.CENTER))
    add_run(p_cap_t22, "Tabela 2.2 – Auditoria Matemática e Métricas Experimentais da Planilha 2 SERIE NATAL.xlsx. Fonte: Elaborado pelo autor (2026).", italic=True, font_size=Pt(9.5))

    # -------------------------------------------------------------
    # 2.1.2 RETROSPECTIVA DA SPRINT
    # -------------------------------------------------------------
    track(make_heading(doc, "2.1.2 Retrospectiva da Sprint", level=3))

    p = track(make_p(doc))
    add_run(p, "Em consonância com as práticas consolidadas do Scrum e os direcionamentos pedagógicos do Projeto Aplicado da XP Educação, "
               "a realização da Retrospectiva da Sprint cumpre o papel crítico de avaliar não apenas os sucessos operacionais alcançados, "
               "mas fundamentalmente ", bold=False)
    add_run(p, "identificar os elementos que não foram plenamente validados ou que revelaram complexidades imprevistas", bold=True)
    add_run(p, ", extraindo aprendizados essenciais para a calibração de rota e o direcionamento prioritário da Sprint 2.", bold=False)

    track(make_heading(doc, "1. O que funcionou com excelência (Pontos Fortes e Validações)", level=4))

    p = track(make_p(doc))
    add_run(p, "•  Validação Plena da Arquitetura Híbrida: ", bold=True)
    add_run(p, "A premissa arquitetural mais arrojada do projeto — confinar os modelos fundacionais de linguagem (LLMs) estritamente à tarefa semântica "
               "de interpretar esquemas e comandos livres, delegando a totalidade das transformações de dados a motores locais determinísticos (Pandas) — "
               "provou ser absolutamente acertada. A auditoria matemática via multiset hash SHA-256 atestou 0,00% de divergência, eliminando integralmente "
               "o maior risco associado à IA generativa em ambientes corporativos: a alucinação de dados numéricos.", bold=False)

    p = track(make_p(doc))
    add_run(p, "•  Autonomia e Eficiência da Heurística de Cabeçalhos: ", bold=True)
    add_run(p, "O algoritmo de scoring multicritério dispensou completamente chamadas de inteligência artificial para localizar a linha de cabeçalho "
               "na presença de ruídos e preâmbulos, executando a varredura em menos de 15 milissegundos e alcançando 100% de acurácia no caso prático.", bold=False)

    p = track(make_p(doc))
    add_run(p, "•  Governança de Privacidade por Design (Privacy by Design): ", bold=True)
    add_run(p, "A rotina de limpeza acoplada às BackgroundTasks do FastAPI cumpriu a política Zero Data Retention sem falhas, comprovando em tempo real "
               "que nenhum registro transacional ou dado nominal de alunos permaneceu em disco após o streaming do arquivo.", bold=False)

    track(make_heading(doc, "2. O que não foi validado, Desafios e Ajustes de Rota (Insights para a Sprint 2)", level=4))

    p = track(make_p(doc))
    add_run(p, "A despeito das validações bem-sucedidas no núcleo central, três descobertas empíricas forneceram insights valiosos que exigiram calibração "
               "imediata no plano de trabalho das sprints seguintes:", bold=False)

    p = track(make_p(doc))
    add_run(p, "•  Insight 1 – Gargalo de I/O em Cargas Sintéticas Elevadas (10.000 linhas): ", bold=True)
    add_run(p, "Durante a execução de baterias de estresse com planilhas sintéticas de 10.000 linhas no ambiente Windows, a latência de processamento local "
               "atingiu 2,14 segundos, situando-se ligeiramente acima do teto estrito de 2,0 segundos almejado na Definição de Pronto da TASK-04. "
               "A investigação revelou que esse acréscimo de tempo não se deveu ao algoritmo mergesort em memória (que consumiu menos de 120 ms), "
               "mas sim ao overhead mecânico de serialização em disco da biblioteca openpyxl ao aplicar estilos célula a célula. "
               "Como ajuste de rota para a Sprint 2, planejou-se otimizar a camada de exportação utilizando buffers voláteis em memória (", bold=False)
    add_run(p, "io.BytesIO", bold=True)
    add_run(p, ") e streaming direto, reduzindo a latência global de serialização.", bold=False)

    p = track(make_p(doc))
    add_run(p, "•  Insight 2 – Complexidade Oculta em Pastas de Trabalho com Múltiplas Abas: ", bold=True)
    add_run(p, "O experimento com ", bold=False)
    add_run(p, "2 SERIE NATAL.xlsx", bold=True)
    add_run(p, " validou a higienização de uma pasta de trabalho com uma única aba ('ALFA'). Contudo, o contato empírico com a secretaria escolar e os analistas de dados "
               "evidenciou que colégios e empresas frequentemente distribuem turmas e filiais em dezenas de abas distintas (ex.: Turmas Alfa, Beta, Gama), "
               "muitas vezes com ligeiras discrepâncias de nomenclatura entre si (ex.: 'NOME DO ALUNO' em uma aba versus 'ESTUDANTE' em outra). "
               "Esse insight confirmou a urgência absoluta de priorizar na Sprint 2 o mecanismo de consolidação multi-abas com alinhamento canônico (TASK-06), "
               "permitindo concatenar verticalmente múltiplas abas heterogêneas em uma tabela unificada com indicação de origem.", bold=False)

    p = track(make_p(doc))
    add_run(p, "•  Insight 3 – A Barreira da Usabilidade para o 'Citizen Data Scientist': ", bold=True)
    add_run(p, "A validação da API via Swagger UI comprovou a perfeição da engenharia de backend, mas escancarou a barreira de adoção humana: "
               "usuários operacionais reais (como secretárias escolares e assistentes financeiros) não operam requisições HTTP RESTful nem JSONs. "
               "Para que o valor do Organizer App se materialize no ambiente de negócios das personas, tornou-se mandatória a entrega na Sprint 2 "
               "de uma interface gráfica web moderna, intuitiva e responsiva em React (TASK-07), provida de área de drag-and-drop, "
               "pré-visualização comparativa Antes x Depois (TASK-08) e badge visual com o Score de Confiança da IA.", bold=False)

    # -------------------------------------------------------------
    # INSERTION INTO DOCUMENT
    # -------------------------------------------------------------
    print(f"Total elements to move: {len(created_elements)}")
    
    # We move all elements from created_elements before target_element
    for el in created_elements:
        target_element.addprevious(el)

    # Now remove old placeholder elements (from idx_start + 1 up to the first new element)
    # Re-find the indices in body
    cur_idx_start = None
    cur_idx_new = None
    
    for i, child in enumerate(body):
        tag = child.tag.split("}")[-1]
        if tag == "p":
            p = docx.text.paragraph.Paragraph(child, doc)
            txt = p.text.strip()
            if "Área de Experimentação" in txt and p.style.name.startswith("Heading 1"):
                cur_idx_start = i
            elif "2.0 Governança Metodológica" in txt:
                cur_idx_new = i
                break

    print(f"Current idx_start: {cur_idx_start}, idx_new: {cur_idx_new}")
    
    elements_to_remove = []
    # Collect elements strictly belonging to the old template
    for i in range(cur_idx_start + 1, cur_idx_new):
        el = body[i]
        tag = el.tag.split("}")[-1]
        if tag == "p":
            txt = docx.text.paragraph.Paragraph(el, doc).text.strip()
            if any(marker in txt for marker in [
                "O que significa esta seção?", "Esta seção tem o objetivo", "É necessário expor",
                "Quais etapas já devem estar", "No momento do preenchimento", "Você também já deve",
                "Como esta seção deve ser", "Esta seção é a área mais", "Evidência da execução de cada",
                "Evidência da solução:", "Para cada Sprint, cite", "Quais ferramentas devem",
                "Obs.: para realização", "2.1 Sprint 1", "2.1.1 Solução", "Evidência dos resultados:",
                "2.1.2 Retrospectiva da Sprint"
            ]) or txt == "":
                elements_to_remove.append(el)

    print(f"Found {len(elements_to_remove)} placeholder elements to remove.")
    for el in elements_to_remove:
        body.remove(el)

    # Save document
    doc.save(doc_path)
    print(f"Document saved successfully to {doc_path}!")

if __name__ == "__main__":
    run()
