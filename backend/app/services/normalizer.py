import re
from datetime import date, datetime
from typing import Any
import pandas as pd


class BrazilianDataNormalizer:
    """
    Módulo de Higienização de Dados Brasileiros (RF-07 / TASK-09).
    Fornece funções para normalização determinística de padrões comuns no ecossistema
    corporativo e contábil brasileiro:
    - Moedas com prefixo R$, separador de milhar '.' e decimal ',';
    - Datas no formato DD/MM/AAAA;
    - Identificadores cadastrais (CPF e CNPJ);
    - Sanitização de espaços em excesso e caracteres invisíveis (\\xa0, \\u200b).
    """

    @staticmethod
    def clean_text(val: Any) -> Any:
        """Remove caracteres invisíveis, espaços duplicados e realiza strip."""
        if val is None or pd.isna(val):
            return val
        s = str(val)
        # Substitui non-breaking spaces e zero-width spaces
        s = s.replace("\xa0", " ").replace("\u200b", "").replace("\ufeff", "")
        # Remove espaços múltiplos
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @staticmethod
    def parse_currency(val: Any) -> float | None:
        """
        Converte strings monetárias no padrão brasileiro para float numérico:
        Exemplos: 'R$ 1.250,50' -> 1250.50, '-R$ 300,00' -> -300.00, '(1.500,00)' -> -1500.00
        """
        if val is None or pd.isna(val):
            return None
        if isinstance(val, (int, float)):
            return float(val)

        s = str(val).strip()
        if not s:
            return None

        # Identifica valores negativos em parênteses ou com sinal de menos
        is_negative = False
        if s.startswith("(") and s.endswith(")"):
            is_negative = True
            s = s[1:-1].strip()
        elif s.startswith("-"):
            is_negative = True
            s = s[1:].strip()

        # Remove prefixo R$, espaços e caracteres não numéricos exceto pontos e vírgulas
        s = re.sub(r"[^\d.,]", "", s)
        if not s:
            return None

        # Se houver pontos e vírgula (ex: 1.234.567,89)
        if "." in s and "," in s:
            s = s.replace(".", "").replace(",", ".")
        # Se houver apenas vírgula (ex: 1250,50)
        elif "," in s:
            s = s.replace(",", ".")
        # Se houver apenas ponto: pode ser milhar (1.250) ou decimal inglês (1250.50)
        elif "." in s:
            parts = s.split(".")
            if len(parts) > 1 and len(parts[-1]) == 3 and len(parts) > 1:
                # Provável separador de milhar brasileiro (ex: 1.000 ou 10.000)
                s = s.replace(".", "")
            else:
                # Mantém como decimal
                pass

        try:
            num = float(s)
            return -num if is_negative else num
        except ValueError:
            return None

    @staticmethod
    def parse_date(val: Any) -> date | None:
        """
        Converte datas no formato brasileiro DD/MM/AAAA para objeto datetime.date.
        Suporta separadores '/', '-', '.' e formatos com ano em 2 ou 4 dígitos.
        """
        if val is None or pd.isna(val):
            return None
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val

        s = str(val).strip()
        if not s:
            return None

        # Formatos comuns brasileiros
        date_patterns = [
            "%d/%m/%Y",
            "%d/%m/%y",
            "%d-%m-%Y",
            "%d-%m-%y",
            "%d.%m.%Y",
            "%Y-%m-%d",  # Formato ISO (fallback)
        ]

        # Tenta extrair primeiro a porção de data se houver hora (ex: 05/01/2026 14:30:00)
        date_part = s.split(" ")[0].strip()

        for fmt in date_patterns:
            try:
                dt = datetime.strptime(date_part, fmt)
                return dt.date()
            except ValueError:
                continue

        return None

    @staticmethod
    def format_cpf(val: Any) -> str | None:
        """Sanitiza e formata string para CPF brasileiro (000.000.000-00)."""
        if val is None or pd.isna(val):
            return None
        digits = re.sub(r"\D", "", str(val))
        if len(digits) != 11:
            return str(val).strip()  # Retorna como está se inválido
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"

    @staticmethod
    def format_cnpj(val: Any) -> str | None:
        """Sanitiza e formata string para CNPJ brasileiro (00.000.000/0000-00)."""
        if val is None or pd.isna(val):
            return None
        digits = re.sub(r"\D", "", str(val))
        if len(digits) != 14:
            return str(val).strip()
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"

    def normalize_dataframe(
        self,
        df: pd.DataFrame,
        currency_columns: list[str] | None = None,
        date_columns: list[str] | None = None,
        cpf_columns: list[str] | None = None,
        cnpj_columns: list[str] | None = None,
        clean_strings: bool = True,
    ) -> pd.DataFrame:
        """
        Aplica a higienização determinística sobre as colunas selecionadas do DataFrame.
        """
        df_out = df.copy()

        if clean_strings:
            for col in df_out.columns:
                if pd.api.types.is_string_dtype(df_out[col]) or df_out[col].dtype in ["object", "str", "string"]:
                    df_out[col] = df_out[col].apply(self.clean_text)

        if currency_columns:
            for col in currency_columns:
                if col in df_out.columns:
                    df_out[col] = df_out[col].apply(self.parse_currency)

        if date_columns:
            for col in date_columns:
                if col in df_out.columns:
                    df_out[col] = df_out[col].apply(self.parse_date)

        if cpf_columns:
            for col in cpf_columns:
                if col in df_out.columns:
                    df_out[col] = df_out[col].apply(self.format_cpf)

        if cnpj_columns:
            for col in cnpj_columns:
                if col in df_out.columns:
                    df_out[col] = df_out[col].apply(self.format_cnpj)

        return df_out


data_normalizer = BrazilianDataNormalizer()
