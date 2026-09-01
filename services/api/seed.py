from datetime import datetime, timezone

if __package__:
    from .database import db, suppliers
    from .seed_data import SUPPLIERS_SEED
else:
    from database import db, suppliers
    from seed_data import SUPPLIERS_SEED


def run_seeder() -> int:
    if len(suppliers) > 0:
        print("La base de datos ya está poblada. No se insertaron registros.")
        return 0

    records = [
        {
            **supplier,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        for supplier in SUPPLIERS_SEED
    ]
    suppliers.insert_multiple(records)

    print(f"Seeder completado: {len(records)} registros insertados.")
    return len(records)


def main() -> None:
    try:
        run_seeder()
    finally:
        db.close()


if __name__ == "__main__":
    main()