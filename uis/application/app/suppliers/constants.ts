import type { SupplierCategory } from "./types";

export const CATEGORY_LABELS: Record<SupplierCategory, string> = {
  carrier_last_mile: "Última milla",
  carrier_international: "Carrier internacional",
  warehouse_supplies: "Suministros de almacén",
  packaging_materials: "Materiales de embalaje",
  reverse_logistics: "Logística inversa",
  fleet_maintenance: "Mantenimiento de flota",
  it_and_wms_software: "Software IT y WMS",
  cleaning_and_facilities: "Limpieza e instalaciones",
};