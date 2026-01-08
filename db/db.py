# database/db.py
import sqlite3
from pathlib import Path
import os
import sys

# =========================
# 1. PATH CHO RESOURCE (READ-ONLY)
# =========================
if getattr(sys, "frozen", False):
    # Khi chạy .exe (PyInstaller)
    RESOURCE_PATH = Path(sys._MEIPASS)
else:
    # Khi chạy source
    RESOURCE_PATH = Path(__file__).parent.parent

SCHEMA_PATH = RESOURCE_PATH / "database" / "schema.sql"

# =========================
# 2. PATH CHO DATA (READ-WRITE)
# =========================
APP_NAME = "RentalManager"

PROJECT_DIR = Path(__file__).parent.parent
DB_PATH = PROJECT_DIR / "rental_manager.db"

# =========================
# 3. KẾT NỐI DB
# =========================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# =========================
# 4. INIT DB TỪ SCHEMA
# =========================
def init_db():
    if DB_PATH.exists():
        return

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy schema.sql tại: {SCHEMA_PATH}"
        )

    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

# =========================
# 5. AUTO INIT
# =========================
init_db()