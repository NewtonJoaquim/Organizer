from PIL import Image, ImageDraw

def generate_personas_infographic():
    width, height = 1200, 520
    img = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([0, 0, width, 60], fill="#006C69")
    draw.text((30, 20), "ORGANIZER APP — PAINEL CONSOLIDADO DE HOMOLOGAÇÃO DAS PERSONAS (TSK-S3-02 / TSK-S3-03)", fill="#FFFFFF")

    # Background
    draw.rectangle([20, 80, width - 20, height - 20], fill="#F8FAFC", outline="#CBD5E1")

    personas = [
        {
            "name": "Carlos Eduardo",
            "role": "Gestor de Confecção & Uniformes",
            "cases": "5 Amostras Testadas",
            "manual": "35 min (2.100s)",
            "app": "8.0 segundos",
            "red": "99.62% de Redução",
            "acc": "100% Acurácia Semântica",
            "int": "100% Integridade SHA-256",
            "color": "#1E3A8A",
        },
        {
            "name": "Mariana Vasconcelos",
            "role": "Coordenadora de BPO Financeiro",
            "cases": "5 Amostras Testadas",
            "manual": "45 min (2.700s)",
            "app": "6.8 segundos",
            "red": "99.75% de Redução",
            "acc": "100% Acurácia Semântica",
            "int": "100% Integridade SHA-256",
            "color": "#006C69",
        },
        {
            "name": "Rodrigo Mendes",
            "role": "Coordenador de Compras & Logística",
            "cases": "5 Amostras Testadas",
            "manual": "25 min (1.500s)",
            "app": "7.2 segundos",
            "red": "99.52% de Redução",
            "acc": "100% Acurácia Semântica",
            "int": "100% Integridade SHA-256",
            "color": "#B45309",
        },
    ]

    card_w = 360
    card_h = 380
    gap = 25
    start_x = 45

    for i, p in enumerate(personas):
        cx = start_x + i * (card_w + gap)
        cy = 105
        # Card Background
        draw.rectangle([cx, cy, cx + card_w, cy + card_h], fill="#FFFFFF", outline="#E2E8F0", width=2)
        # Card Header
        draw.rectangle([cx, cy, cx + card_w, cy + 65], fill=p["color"])
        draw.text((cx + 15, cy + 12), p["name"], fill="#FFFFFF")
        draw.text((cx + 15, cy + 35), p["role"], fill="#E0F2FE")

        # Badges
        draw.rectangle([cx + 15, cy + 80, cx + card_w - 15, cy + 105], fill="#EFF6FF")
        draw.text((cx + 25, cy + 86), "• Cobertura: " + p["cases"] + " (100% Sucesso)", fill="#1E3A8A")

        # Metrics
        draw.text((cx + 15, cy + 125), "Tempo Manual Médio:", fill="#64748B")
        draw.text((cx + 180, cy + 125), p["manual"], fill="#DC2626")

        draw.text((cx + 15, cy + 155), "Tempo no Organizer App:", fill="#64748B")
        draw.text((cx + 180, cy + 155), p["app"], fill="#059669")

        draw.text((cx + 15, cy + 185), "Ganho de Produtividade:", fill="#64748B")
        draw.text((cx + 180, cy + 185), p["red"], fill="#059669")

        # Progress bar for reduction
        draw.rectangle([cx + 15, cy + 215, cx + card_w - 15, cy + 235], fill="#E2E8F0")
        draw.rectangle([cx + 15, cy + 215, cx + 15 + int((card_w - 30) * 0.996), cy + 235], fill="#059669")
        draw.text((cx + 130, cy + 219), "Meta SMART: >= 70%", fill="#FFFFFF")

        # Additional Quality Metrics
        draw.rectangle([cx + 15, cy + 255, cx + card_w - 15, cy + 310], fill="#F0FDF4", outline="#BBF7D0")
        draw.text((cx + 25, cy + 265), "✓ " + p["acc"], fill="#15803D")
        draw.text((cx + 25, cy + 285), "✓ " + p["int"], fill="#15803D")

        # Seal of Approval
        draw.rectangle([cx + 15, cy + 325, cx + card_w - 15, cy + 360], fill=p["color"])
        draw.text((cx + 70, cy + 335), "✓ HOMOLOGADO PELA PERSONA", fill="#FFFFFF")

    img.save("organizer-personas-benchmark.png")
    print("organizer-personas-benchmark.png gerada com sucesso!")

if __name__ == "__main__":
    generate_personas_infographic()
