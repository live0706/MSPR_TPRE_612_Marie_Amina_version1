import json
from pathlib import Path

from fastapi import HTTPException, status

from database import get_engine


def ensure_db() -> None:
    try:
        get_engine()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de donnees non connectee.",
        ) from exc


def read_json_file(path):
    file_path = Path(path)
    if not file_path.exists():
        return None
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
