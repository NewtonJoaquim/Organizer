import json
import logging
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.core.security import (
    sanitize_filename,
    validate_file_extension,
    validate_magic_bytes,
)
from app.schemas.upload import UploadResponse

CHUNK_SIZE = 64 * 1024  # 64 KB por chunk
logger = logging.getLogger("organizer.lgpd")


class FileService:
    def __init__(self, temp_dir: Path | None = None) -> None:
        self.temp_dir = temp_dir or settings.TEMP_STORAGE_DIR
        self._associations: dict[str, str] = {}
        self._ensure_temp_dir()

    def _ensure_temp_dir(self) -> None:
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def count_active_directories(self) -> int:
        """Retorna a contagem de diretórios temporários ativos em disco."""
        if not self.temp_dir.exists():
            return 0
        return sum(1 for item in self.temp_dir.iterdir() if item.is_dir())

    def associate_files(self, processed_file_id: str, original_file_id: str) -> None:
        """
        Registra a correlação entre o arquivo processado e seu arquivo de upload original,
        permitindo a destruição atômica conjunta após o download (Zero Data Retention).
        """
        self._associations[processed_file_id] = original_file_id
        target_dir = self.temp_dir / processed_file_id
        if target_dir.exists():
            meta_path = target_dir / "meta.json"
            try:
                meta_path.write_text(
                    json.dumps({
                        "processed_file_id": processed_file_id,
                        "original_file_id": original_file_id,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }),
                    encoding="utf-8",
                )
            except Exception as e:
                logger.warning(f"Falha ao persistir metadados de ciclo de vida em {target_dir}: {e}")

    def get_associated_file(self, processed_file_id: str) -> str | None:
        """Recupera o ID do upload original associado ao arquivo processado."""
        if processed_file_id in self._associations:
            return self._associations[processed_file_id]

        meta_path = self.temp_dir / processed_file_id / "meta.json"
        if meta_path.exists():
            try:
                data = json.loads(meta_path.read_text(encoding="utf-8"))
                orig_id = data.get("original_file_id")
                if orig_id:
                    self._associations[processed_file_id] = orig_id
                    return orig_id
            except Exception:
                pass
        return None

    def cleanup_workflow(self, processed_file_id: str) -> dict[str, Any]:
        """
        Expurga imediatamente os resíduos em disco após a conclusão do download pelo cliente (DoD TSK-S1-05).
        Remove tanto o arquivo processado (.xlsx) quanto o arquivo bruto original de upload.
        Garante conformidade estrita com Zero Data Retention (RN-04 e RNF-03).
        """
        orig_file_id = self.get_associated_file(processed_file_id)

        # 1. Remove diretório processado
        proc_dir = (self.temp_dir / processed_file_id).resolve()
        if proc_dir.exists() and proc_dir.is_relative_to(self.temp_dir.resolve()):
            shutil.rmtree(proc_dir, ignore_errors=True)

        # 2. Remove diretório de upload original se associado
        if orig_file_id:
            orig_dir = (self.temp_dir / orig_file_id).resolve()
            if orig_dir.exists() and orig_dir.is_relative_to(self.temp_dir.resolve()):
                shutil.rmtree(orig_dir, ignore_errors=True)
            self._associations.pop(processed_file_id, None)

        remaining = self.count_active_directories()

        logger.info(
            f"[LGPD-AUDIT] Descarte imediato pós-download concluído. "
            f"processed_file_id='{processed_file_id}', original_file_id='{orig_file_id}'. "
            f"Diretórios ativos restantes em disco: {remaining}."
        )

        return {
            "processed_file_id": processed_file_id,
            "original_file_id": orig_file_id,
            "remaining_directories": remaining,
            "zero_data_retention": remaining == 0,
        }

    async def save_upload_file(self, file: UploadFile) -> UploadResponse:
        """
        Recebe um UploadFile, valida extensão, sanitiza o nome, verifica magic bytes
        e salva de forma segura aplicando streaming com limite estrito de tamanho (20 MB).
        """
        raw_filename = file.filename or "planilha.xlsx"
        ext = validate_file_extension(raw_filename)
        safe_filename = sanitize_filename(raw_filename)

        file_id = str(uuid.uuid4())
        target_dir = self.temp_dir / file_id
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / safe_filename

        total_bytes = 0
        first_chunk = True

        try:
            with open(file_path, "wb") as out_file:
                while chunk := await file.read(CHUNK_SIZE):
                    total_bytes += len(chunk)

                    # Validação de tamanho máximo (RF-01: máximo 20 MB)
                    if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
                        raise HTTPException(
                            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                            detail=(
                                f"Arquivo excede o limite máximo permitido de "
                                f"{settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
                            ),
                        )

                    # Validação de integridade nos primeiros bytes (Magic Bytes)
                    if first_chunk:
                        validate_magic_bytes(chunk[:16], ext)
                        first_chunk = False

                    out_file.write(chunk)

            # Caso o arquivo esteja completamente vazio
            if total_bytes == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Arquivo de upload está vazio (0 bytes).",
                )

        except Exception:
            # Em caso de erro ou limite estourado, destrói resíduos imediatamente (Zero Data Retention)
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            raise

        return UploadResponse(
            file_id=file_id,
            original_filename=raw_filename,
            sanitized_filename=safe_filename,
            size_bytes=total_bytes,
            content_type=file.content_type or "application/octet-stream",
            extension=ext,
            created_at=datetime.now(timezone.utc),
            message="Planilha recebida e validada com integridade de bytes.",
        )

    def get_file_path(self, file_id: str, filename: str | None = None) -> Path:
        """
        Retorna o caminho do arquivo temporário isolado, validando que não ocorra escape do diretório.
        """
        target_dir = (self.temp_dir / file_id).resolve()
        if not target_dir.exists() or not target_dir.is_relative_to(self.temp_dir.resolve()):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Arquivo com ID '{file_id}' não encontrado.",
            )

        if filename:
            file_path = (target_dir / sanitize_filename(filename)).resolve()
            if not file_path.exists() or not file_path.is_relative_to(target_dir):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Arquivo '{filename}' não encontrado para o ID '{file_id}'.",
                )
            return file_path

        # Se filename não foi especificado, retorna o primeiro arquivo presente na pasta
        files = list(target_dir.glob("*"))
        if not files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nenhum arquivo encontrado no diretório do ID '{file_id}'.",
            )
        return files[0]

    def cleanup_file(self, file_id: str) -> bool:
        """
        Remove imediatamente o diretório temporário e os arquivos do file_id (LGPD / Zero Retention).
        """
        target_dir = (self.temp_dir / file_id).resolve()
        if target_dir.exists() and target_dir.is_relative_to(self.temp_dir.resolve()):
            shutil.rmtree(target_dir, ignore_errors=True)
            return True
        return False

    def purge_expired_files(self, ttl_minutes: int | None = None) -> int:
        """
        Remove arquivos temporários que ultrapassaram o tempo limite de vida (RN-04: TTL 15 minutos).
        Gera evidência auditável nos logs da governança LGPD.
        """
        ttl_seconds = (ttl_minutes or settings.TEMP_FILE_TTL_MINUTES) * 60
        now = time.time()
        purged = 0

        if not self.temp_dir.exists():
            return 0

        for item in self.temp_dir.iterdir():
            if item.is_dir():
                try:
                    mtime = item.stat().st_mtime
                    if (now - mtime) > ttl_seconds:
                        shutil.rmtree(item, ignore_errors=True)
                        purged += 1
                        logger.info(f"[LGPD-TTL-PURGE] Diretório expirado expurgado: '{item.name}'.")
                except Exception as e:
                    logger.warning(f"Erro ao purgar diretório expirado '{item.name}': {e}")

        remaining = self.count_active_directories()
        if purged > 0:
            logger.info(
                f"[LGPD-AUDIT] Rotina periódica TTL concluída: {purged} diretórios expurgados. "
                f"Diretórios restantes em disco: {remaining}."
            )

        return purged


file_service = FileService()
