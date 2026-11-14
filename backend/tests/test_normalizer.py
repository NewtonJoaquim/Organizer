from datetime import date
import pandas as pd
from app.services.normalizer import data_normalizer


def test_clean_text_removes_invisible_characters():
    dirty_text = "  Relatório\xa0Mensal \u200b com espaços   duplos\ufeff  "
    cleaned = data_normalizer.clean_text(dirty_text)
    assert cleaned == "Relatório Mensal com espaços duplos"


def test_parse_brazilian_currency():
    assert data_normalizer.parse_currency("R$ 1.250,50") == 1250.50
    assert data_normalizer.parse_currency("R$   3.500,00") == 3500.00
    assert data_normalizer.parse_currency("- R$ 450,25") == -450.25
    assert data_normalizer.parse_currency("(1.200,00)") == -1200.00
    assert data_normalizer.parse_currency("1250,50") == 1250.50
    assert data_normalizer.parse_currency("1000") == 1000.00
    assert data_normalizer.parse_currency(1500.75) == 1500.75
    assert data_normalizer.parse_currency("") is None


def test_parse_brazilian_date():
    assert data_normalizer.parse_date("05/01/2026") == date(2026, 1, 5)
    assert data_normalizer.parse_date("28/02/26") == date(2026, 2, 28)
    assert data_normalizer.parse_date("15-08-2025") == date(2025, 8, 15)
    assert data_normalizer.parse_date("10.12.2024") == date(2024, 12, 10)
    assert data_normalizer.parse_date("2026-11-08") == date(2026, 11, 8)
    assert data_normalizer.parse_date("05/01/2026 14:30:00") == date(2026, 1, 5)
    assert data_normalizer.parse_date("texto_invalido") is None


def test_format_cpf():
    assert data_normalizer.format_cpf("12345678901") == "123.456.789-01"
    assert data_normalizer.format_cpf("123.456.789-01") == "123.456.789-01"
    assert data_normalizer.format_cpf("12345") == "12345"  # Inválido mantém original


def test_format_cnpj():
    assert data_normalizer.format_cnpj("12345678000195") == "12.345.678/0001-95"
    assert data_normalizer.format_cnpj("12.345.678/0001-95") == "12.345.678/0001-95"


def test_normalize_dataframe():
    df = pd.DataFrame({
        "fornecedor": ["  Empresa\xa0A  ", "Empresa B\u200b"],
        "valor": ["R$ 1.250,50", "(350,00)"],
        "data_vencimento": ["05/01/2026", "15/02/2026"],
        "documento": ["12345678901", "12345678000195"],
    })

    normalized = data_normalizer.normalize_dataframe(
        df,
        currency_columns=["valor"],
        date_columns=["data_vencimento"],
        cpf_columns=["documento"],
        clean_strings=True,
    )

    assert normalized["fornecedor"].tolist() == ["Empresa A", "Empresa B"]
    assert normalized["valor"].tolist() == [1250.50, -350.00]
    assert normalized["data_vencimento"].tolist() == [date(2026, 1, 5), date(2026, 2, 15)]
    assert normalized["documento"].iloc[0] == "123.456.789-01"
