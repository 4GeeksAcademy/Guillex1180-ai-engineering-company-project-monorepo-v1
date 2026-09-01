import os
import random
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

from tinydb import TinyDB

if __package__:
    from .database import db, suppliers
    from .models import SupplierCreate, VALID_CATEGORIES
else:
    from database import db, suppliers
    from models import SupplierCreate, VALID_CATEGORIES


TOTAL_SUPPLIERS = 100
DEFAULT_RANDOM_SEED = 20260901

COUNTRY_SETTINGS = {
    "USA": {
        "currency": "USD",
        "zones": [
            "West Coast",
            "East Coast",
            "Texas",
            "Midwest",
            "Pacific Northwest",
            "Continental USA",
        ],
        "locations": [
            "Los Angeles",
            "Seattle",
            "Austin",
            "Chicago",
            "Atlanta",
            "Denver",
        ],
        "suffixes": ["Logistics", "Solutions", "Services", "Group", "Systems"],
    },
    "Spain": {
        "currency": "EUR",
        "zones": [
            "Aragón",
            "Península Ibérica",
            "Madrid",
            "Cataluña",
            "Zona Norte",
            "Andalucía",
        ],
        "locations": [
            "Zaragoza",
            "Madrid",
            "Barcelona",
            "Bilbao",
            "Valencia",
            "Sevilla",
        ],
        "suffixes": ["Logística", "Transportes", "Servicios", "Sistemas", "S.L."],
    },
}

CATEGORY_NAMES = {
    "carrier_last_mile": [
        "RapidRoute",
        "UrbanParcel",
        "FinalMile",
        "MetroCourier",
        "DirectDispatch",
    ],
    "carrier_international": [
        "GlobalFreight",
        "Atlantic Cargo",
        "WorldBridge",
        "InterLink Express",
        "CrossBorder Transit",
    ],
    "warehouse_supplies": [
        "Warehouse Depot",
        "StockRoom Supply",
        "Industrial Source",
        "Dockside Equipment",
        "Fulfillment Supply",
    ],
    "packaging_materials": [
        "PackWorks",
        "BoxCraft",
        "SecureWrap",
        "EcoPackaging",
        "Parcel Materials",
    ],
    "reverse_logistics": [
        "ReturnPath",
        "ReverseFlow",
        "LoopBack",
        "ReturnPoint",
        "Circular Transit",
    ],
    "fleet_maintenance": [
        "FleetCare",
        "VehicleWorks",
        "Transit Garage",
        "RoadReady",
        "Fleet Mechanics",
    ],
    "it_and_wms_software": [
        "WMS Cloud",
        "StockPilot",
        "FulfillTech",
        "Warehouse Logic",
        "Inventory Systems",
    ],
    "cleaning_and_facilities": [
        "FacilityCare",
        "CleanDock",
        "Warehouse Hygiene",
        "Site Services",
        "Industrial Clean",
    ],
}

RATE_RANGES = {
    "carrier_last_mile": (3.50, 12.00),
    "carrier_international": (12.00, 25.00),
    "warehouse_supplies": (15.00, 250.00),
    "packaging_materials": (0.15, 3.50),
    "reverse_logistics": (4.00, 18.00),
    "fleet_maintenance": (250.00, 1800.00),
    "it_and_wms_software": (500.00, 3500.00),
    "cleaning_and_facilities": (500.00, 3500.00),
}

ACTIVE_NOTES = [
    "Carrier de respaldo para picos de demanda.",
    "Tarifa negociada por volumen Q3.",
    "Contrato revisado por el equipo de operaciones.",
    "Proveedor prioritario para servicios urgentes.",
    "Buen desempeño durante el último trimestre.",
]

SUSPENDED_NOTES = [
    "Suspendido por retrasos recurrentes.",
    "Suspendido por tasa de incidencias elevada.",
    "Contrato en revisión por incumplimiento de SLA.",
    "Suspendido temporalmente por problemas de capacidad.",
]


def _email_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_value.lower())


def _rate_for_category(category: str, generator: random.Random) -> float:
    minimum, maximum = RATE_RANGES[category]
    return round(generator.uniform(minimum, maximum), 2)


def generate_suppliers(
    count: int = TOTAL_SUPPLIERS,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> list[dict[str, Any]]:
    if count != TOTAL_SUPPLIERS:
        raise ValueError(f"This bulk seeder must generate exactly {TOTAL_SUPPLIERS} suppliers")

    generator = random.Random(random_seed)
    countries = ["USA"] * 50 + ["Spain"] * 50
    statuses = ["active"] * 80 + ["suspended"] * 20
    generator.shuffle(countries)
    generator.shuffle(statuses)

    records: list[dict[str, Any]] = []
    for index, (country, status) in enumerate(zip(countries, statuses), start=1):
        category_count = 2 if generator.random() < 0.28 else 1
        categories = generator.sample(VALID_CATEGORIES, k=category_count)
        primary_category = categories[0]
        settings = COUNTRY_SETTINGS[country]
        location = generator.choice(settings["locations"])
        company_root = generator.choice(CATEGORY_NAMES[primary_category])
        company_suffix = generator.choice(settings["suffixes"])
        name = f"{company_root} {location} {company_suffix} {index:03d}"
        email_domain = _email_slug(name)

        record: dict[str, Any] = {
            "name": name,
            "country": country,
            "categories": categories,
            "rate_per_shipment": _rate_for_category(primary_category, generator),
            "currency": settings["currency"],
            "status": status,
            "service_zone": generator.choice(settings["zones"]),
            "contact_email": f"contacto@{email_domain}.com",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if generator.random() < 0.75:
            notes = SUSPENDED_NOTES if status == "suspended" else ACTIVE_NOTES
            record["notes"] = generator.choice(notes)

        validated = SupplierCreate.model_validate(
            {key: value for key, value in record.items() if key != "updated_at"}
        )
        records.append(
            {
                **validated.model_dump(mode="json", exclude_none=True),
                "updated_at": record["updated_at"],
            }
        )

    return records


def run_bulk_seeder(database: TinyDB = db) -> int:
    table = suppliers if database is db else database.table("suppliers")
    random_seed = int(os.getenv("SEED_100_RANDOM_SEED", DEFAULT_RANDOM_SEED))
    records = generate_suppliers(random_seed=random_seed)

    table.truncate()
    table.insert_multiple(records)

    print(
        "Carga masiva completada: "
        f"{len(records)} proveedores insertados exitosamente en TinyDB."
    )
    return len(records)


def main() -> None:
    try:
        run_bulk_seeder()
    finally:
        db.close()


if __name__ == "__main__":
    main()