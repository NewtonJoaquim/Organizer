import re
from pathlib import Path
from fastapi import HTTPException, status
from app.core.config import settings

# Magic bytes (file signatures)
# XLSX: ZIP archive starts with PK\x03\x04
XLSX_MAGIC_BYTES = b"PK\x03\x04"
# XLS: Microsoft Compound File Binary (CFB / OLE2) starts with \xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1
XLS_MAGIC_BYTES = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def sanitize_filename(filename: str | None) -> str:
    """
    Sanitiza o nome do arquivo para mitigar ataques de Path Traversal e injeção de caracteres perigosos.
    - Remove referências a diretórios superiores (../, ..\\)
    - Remove caminhos absolutos e barras (/ e \\)
    - Remove caracteres nulos e de controle
    - Mantém apenas caracteres alfanuméricos, pontos, hífens e underscores
    - Garante que a extensão seja preservada de forma limpa
    """
    if not filename:
        return "unnamed_spreadsheet.xlsx"

    # Pega apenas o basename, ignorando qualquer prefixo de caminho
    base_name = Path(filename).name

    # Remove caracteres nulos e barras
    base_name = base_name.replace("\x00", "").replace("/", "").replace("\\", "")

    # Substitui caracteres não alfanuméricos (exceto . - _) por underscore
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", base_name)

    # Evita nomes ocultos ou relativos iniciando com ponto
    sanitized = sanitized.lstrip(".")

    # Reduz underscores ou pontos múltiplos
    sanitized = re.sub(r"_{2,}", "_", sanitized)

    if not sanitized:
        return "spreadsheet.xlsx"

    return sanitized


def validate_file_extension(filename: str) -> str:
    """
    Valida se a extensão do arquivo pertence à lista autorizada (.xlsx ou .xls).
    Retorna a extensão em minúsculas ou lança HTTPException(400).
    """
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Formato de arquivo não suportado: '{ext}'. "
                f"Formatos aceitos: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}."
            ),
        )
    return ext


def validate_magic_bytes(header: bytes, ext: str) -> None:
    """
    Verifica a assinatura binária (magic bytes) para garantir a integridade do arquivo.
    Evita que arquivos executáveis ou scripts sejam renomeados para .xlsx/.xls.
    """
    if ext == ".xlsx":
        if not header.startswith(XLSX_MAGIC_BYTES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo inválido: a assinatura binária não corresponde a uma planilha OpenXML (.xlsx) legítima.",
            )
    elif ext == ".xls":
        if not header.startswith(XLS_MAGIC_BYTES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo inválido: a assinatura binária não corresponde a uma planilha legada (.xls) legítima.",
            )
