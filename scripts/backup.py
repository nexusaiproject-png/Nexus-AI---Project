from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def backup_database(source: str | Path, destination_dir: str | Path) -> Path:
    src = Path(source)
    dest = Path(destination_dir)
    if not src.is_file():
        raise FileNotFoundError(src)
    dest.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = dest / f"nexus-{stamp}.db"
    with sqlite3.connect(src) as source_db, sqlite3.connect(target) as target_db:
        source_db.backup(target_db)
    os.chmod(target, 0o600)
    return target


if __name__ == "__main__":
    source = os.environ.get("NEXUS_DB_PATH", "data/auth.db")
    destination = os.environ.get("NEXUS_BACKUP_DIR", "backups")
    print(backup_database(source, destination))
