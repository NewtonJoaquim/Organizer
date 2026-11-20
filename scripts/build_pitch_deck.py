import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def build_pitch():
    template_path = Path("Template - Pitch.pptx")
    output_path = Path("Pitch do Projeto Aplicado.pptx")

    prs = Presentation(str(template_path))
    print(f"Loaded template with {len(prs.slides)} slides.")

    # -----------------------------------------------------------------
    # SLIDE 1: CAPA
    # -----------------------------------------------------------------
    s1 = prs.slides[0]
    for shape in s1.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                if "<inserir título do projeto>" in p.text:
                    p.text = "ORGANIZER APP: Organizador Inteligente de Dados e Planilhas"
                    p.font.bold = True
                elif "<inserir nome do aluno>" in p.text:
                    p.text = "Newton Joaquim • Pós-Graduação em Inteligência Artificial e Engenharia de Software • XP Educação"
                    p.font.size = Pt(14)

    # -----------------------------------------------------------------
    # SLIDE 3: APRESENTAÇÃO
    # -----------------------------------------------------------------
    s3 = prs.slides[2]
    for shape in s3.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                if "Descreva aqui um breve relato sobre quem é você" in p.text:
                    shape.text_frame.text = (
                        "Newton Joaquim — Engenheiro de Software e Pós-Graduando em Inteligência Artificial "
                        "e Engenharia de Software pela XP Educação (XPE).\n\n"
                        "Atuação profissional focada em arquitetura de dados corporativos, microsserviços distribuídos, "
                        "integração de modelos de linguagem (LLMs) em sistemas de alta confiabilidade e automação de "
                        "processos de missão crítica com tolerância zero a falhas.\n\n"
                        "LinkedIn: linkedin.com/in/newton-joaquim\n"
                        "GitHub: github.com/NewtonJoaquim/Organizer"
                    )
                    for para in shape.text_frame.paragraphs:
                        para.font.size = Pt(13)
                        para.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

    # -----------------------------------------------------------------
    # SLIDE 4: DESAFIO
    # -----------------------------------------------------------------
    s4 = prs.slides[3]
    for shape in s4.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                if "Descreva aqui a contextualização do desafio" in p.text:
                    shape.text_frame.text = (
                        "• O Cenário de Dor: Analistas de negócios e operadores perdem de 30% a 40% de sua jornada semanal "
                        "em tarefas manuais de limpeza, recorte de preâmbulos e ordenação de planilhas Excel heterogêneas.\n\n"
                        "• O Risco Corporativo: A manipulação manual por 'copia-e-cola' gera frequentes erros de digitação, "
                        "alucinações humanas, atrasos no fechamento contábil e risco de violação à LGPD ao enviar dados sensíveis à nuvem.\n\n"
                        "• Personas e Dores Reais Homologadas no Projeto:\n"
                        "  - Carlos (Confecção & Uniformes): Grades com preâmbulos e tamanhos mistos travam o corte fabril.\n"
                        "  - Mariana (BPO Financeiro): Extratos bancários com formatos distintos de dezenas de clientes PMEs.\n"
                        "  - Rodrigo (Compras & Logística): Tabelas de fretes e cotações de fornecedores incompatíveis entre si."
                    )
                    for para in shape.text_frame.paragraphs:
                        para.font.size = Pt(12)
                        para.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)

    # -----------------------------------------------------------------
    # SLIDE 5: SOLUÇÃO & OBJETIVO SMART
    # -----------------------------------------------------------------
    s5 = prs.slides[4]
    for shape in s5.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                if "Descreva aqui um breve relato sobre solução proposta" in p.text:
                    shape.text_frame.text = (
                        "• Proposta de Engenharia: Plataforma horizontal e agnóstica a dados com arquitetura híbrida desacoplada:\n"
                        "  1. Camada Semântica (IA): Interpreta instruções em português e padroniza cabeçalhos enviando apenas metadados.\n"
                        "  2. Motor Determinístico Local: Ordenação mergesort estável via Pandas local com 100% de integridade matemática.\n"
                        "  3. Interfaces de Adoção: Aplicação Web SPA responsiva (React 19) e Suplemento Nativo (Microsoft Excel Add-in).\n\n"
                        "• Objetivo SMART Alcançado: Automatizar a higienização e ordenação de planilhas de até 10.000 linhas em menos de 15 segundos, "
                        "com acurácia semântica ≥ 90%, zero retenção de dados temporários e redução do tempo de manipulação manual comprovada em ≥ 70%."
                    )
                    for para in shape.text_frame.paragraphs:
                        para.font.size = Pt(11.5)
                        para.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)

    # -----------------------------------------------------------------
    # SLIDE 6: DIFERENCIAIS COMPETITIVOS
    # -----------------------------------------------------------------
    s6 = prs.slides[5]
    for shape in s6.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                if "Descreva aqui em tópicos os principais diferencias" in p.text:
                    shape.text_frame.text = (
                        "• Confiabilidade Matemática Estrita (Zero Alucinação): A IA nunca gera ou manipula os valores das células. "
                        "Toda ordenação é executada por algoritmos locais estáveis com validação por hash multiset SHA-256 (RNF-02).\n\n"
                        "• Privacidade por Design & LGPD (Zero Data Retention): Apenas os nomes das colunas trafegam para a IA. "
                        "Nenhum registro sensível de cliente sai da infraestrutura local e os arquivos temporários são excluídos imediatamente pós-download.\n\n"
                        "• Canal Nativo Integrado (Microsoft Excel Add-in): Leitura da seleção ativa e devolução organizada diretamente na planilha sem alternar de janelas.\n\n"
                        "• Eficiência Extrema de Custos (Unit Economics): Média de 550 tokens por requisição (R$ 0,0011 por chamada), garantindo margem bruta de 98,4%."
                    )
                    for para in shape.text_frame.paragraphs:
                        para.font.size = Pt(12)
                        para.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)

    # -----------------------------------------------------------------
    # SLIDE 7: DESENVOLVIMENTO ÁGIL (3 SPRINTS / 21 DIAS)
    # -----------------------------------------------------------------
    s7 = prs.slides[6]
    for shape in s7.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                if "sprint 1 e sua retrospectiva" in p.text:
                    shape.text_frame.text = (
                        "Sprint 1: Núcleo e Segurança (20 pts)\n"
                        "• Setup backend FastAPI e ingestão multipart (.xlsx e .xls até 20 MB).\n"
                        "• Detecção heurística de cabeçalhos eliminando preâmbulos sujos.\n"
                        "• Orquestrador semântico com LLM e Pydantic Structured Outputs.\n"
                        "• Motor mergesort e auditoria hash multiset SHA-256 (RNF-02).\n"
                        "• Política de descarte imediato pós-download e governança LGPD."
                    )
                    for para in shape.text_frame.paragraphs:
                        para.font.size = Pt(10)
                elif "sprint 2 e sua retrospectiva" in p.text:
                    shape.text_frame.text = (
                        "Sprint 2: Consolidação e UX (18 pts)\n"
                        "• Merge determinístico e unificação vertical de múltiplas abas heterogêneas.\n"
                        "• Construção da interface SPA moderna em React 19 + TypeScript + Tailwind.\n"
                        "• Tela de Pré-Visualização Antes x Depois com score de confiança da IA.\n"
                        "• Módulo de higienização de formatos brasileiros (R$, datas, CPFs, CNPJs).\n"
                        "• Validação prática na planilha corporativa real 2 SERIE SUL.xlsx."
                    )
                    for para in shape.text_frame.paragraphs:
                        para.font.size = Pt(10)
                elif "sprint 3 e sua retrospectiva" in p.text:
                    shape.text_frame.text = (
                        "Sprint 3: Canais e Homologação (16 pts)\n"
                        "• Prototipação do Suplemento Nativo Microsoft Excel Add-in (Office.js).\n"
                        "• Bateria experimental com 15 amostras das 3 personas (100% acerto).\n"
                        "• Testes de carga: 10.000 linhas processadas em 2,4s (SLA < 15s OK).\n"
                        "• Redução do tempo manual comprovada de 99,5% a 99,75% (meta >= 70%).\n"
                        "• Consolidação do Relatório Técnico (.docx) e apresentação do Pitch."
                    )
                    for para in shape.text_frame.paragraphs:
                        para.font.size = Pt(10)

    # -----------------------------------------------------------------
    # SLIDE 8: RESULTADOS, LIÇÕES APRENDIDAS E PRÓXIMOS PASSOS
    # -----------------------------------------------------------------
    s8 = prs.slides[7]
    for shape in s8.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                if "Item 1:" in p.text:
                    p.text = "1. Expansão Multimodal com Docling (Sprint 4):"
                    p.font.bold = True
                elif "Item 2:" in p.text:
                    p.text = "2. Publicação Comercial no Microsoft AppSource:"
                    p.font.bold = True
                elif "Item 3:" in p.text:
                    p.text = "3. Conectores Nativos para ERPs Corporativos:"
                    p.font.bold = True

            txt_full = shape.text_frame.text
            if "Descreva um item que será considerado como próximo passo" in txt_full:
                # Substitui os blocos de próximos passos
                pass

    # Atualiza caixas de texto específicas dos itens no Slide 8
    for shape in s8.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text.strip()
            if "Descreva um item que será considerado como próximo passo do seu projeto." in text:
                shape.text_frame.text = (
                    "Ingestão e extração tabular de documentos em formato PDF escaneados e arquivos heterogêneos (.docx, .pptx) "
                    "via motor TableFormer da biblioteca Docling (RF-11 e RF-12), normalizando tabelas diretamente para o pipeline determinístico."
                )
                for para in shape.text_frame.paragraphs:
                    para.font.size = Pt(10.5)
                break

    # -----------------------------------------------------------------
    # SLIDE 9: ENCERRAMENTO
    # -----------------------------------------------------------------
    s9 = prs.slides[8]
    for shape in s9.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                if "Obrigado(a)!" in p.text:
                    shape.text_frame.text = (
                        "Muito Obrigado!\n\n"
                        "Newton Joaquim — Projeto Aplicado Organizer App\n"
                        "Pós-Graduação em Inteligência Artificial e Engenharia de Software\n"
                        "XP Educação (XPE) — Novembro de 2026\n\n"
                        "Repositório Oficial: github.com/NewtonJoaquim/Organizer\n"
                        "Quadro Kanban: github.com/users/NewtonJoaquim/projects/1/views/1"
                    )
                    for para in shape.text_frame.paragraphs:
                        if "Muito Obrigado!" in para.text:
                            para.font.size = Pt(28)
                            para.font.bold = True
                            para.font.color.rgb = RGBColor(0x00, 0x6C, 0x69)
                        else:
                            para.font.size = Pt(13)
                            para.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

    prs.save(str(output_path))
    print(f"Apresentação executiva salva com sucesso em: {output_path}")

if __name__ == "__main__":
    build_pitch()
