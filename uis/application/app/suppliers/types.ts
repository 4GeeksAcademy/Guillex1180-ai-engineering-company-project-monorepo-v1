export const VALID_CATEGORIES = [
  "carrier_last_mile",
  "carrier_international",
  "warehouse_supplies",
  "packaging_materials",
  "reverse_logistics",
  "fleet_maintenance",
  "it_and_wms_software",
  "cleaning_and_facilities",
] as const;

export type SupplierCategory = (typeof VALID_CATEGORIES)[number];
export type SupplierCountry = "USA" | "Spain";
export type SupplierCurrency = "USD" | "EUR";
export type SupplierStatus = "active" | "suspended";

export interface Supplier {
  id: number;
  name: string;
  country: SupplierCountry;
  categories: SupplierCategory[];
  rate_per_shipment: number;
  currency: SupplierCurrency;
  status: SupplierStatus;
  updated_at: string;
  service_zone: string | null;
  contact_email: string | null;
  notes: string | null;
}

export interface SupplierCreate {
  name: string;
  country: SupplierCountry;
  categories: SupplierCategory[];
  rate_per_shipment: number;
  currency: SupplierCurrency;
  status: SupplierStatus;
  service_zone?: string;
  contact_email?: string;
  notes?: string;
}

export interface SupplierFilters {
  country?: SupplierCountry;
  category?: SupplierCategory;
}