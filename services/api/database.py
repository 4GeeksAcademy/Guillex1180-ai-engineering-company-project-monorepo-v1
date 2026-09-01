import os
from pathlib import Path

from tinydb import TinyDB


DATABASE_PATH = Path(
    os.getenv("TINYDB_PATH", Path(__file__).parent / "data" / "db.json")
)
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

db = TinyDB(DATABASE_PATH)
suppliers = db.table("suppliers")