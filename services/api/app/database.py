"""Re-export de la sesión SQLAlchemy desde el módulo padre ``database.py``.

Este módulo puente permite que los routers dentro del paquete ``app/``
importen ``get_db``, ``engine`` y ``SessionLocal`` con imports relativos
sin romper la estructura de paquetes.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Import desde el módulo padre (services/api/database.py)
_parent = Path(__file__).resolve().parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

# mypy: disable-error-code="import-unused"
try:
    from database import get_db, engine, SessionLocal  # type: ignore[import-unrecognized]
except ImportError:
    import importlib

    _spec = importlib.util.spec_from_file_location(
        "database", _parent / "database.py"
    )
    if _spec and _spec.loader:
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        get_db = _mod.get_db
        engine = _mod.engine
        SessionLocal = _mod.SessionLocal
    else:
        raise

__all__ = ["engine", "get_db", "SessionLocal"]