import json
from pathlib import Path

from fastapi import HTTPException

from database import engine


def ensure_db():
    if engine is None:
        raise HTTPException(status_code=500, detail="Base de donnees non connectee.")


def read_json_file(path):
    file_path = Path(path)
    if not file_path.exists():
        return None
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
