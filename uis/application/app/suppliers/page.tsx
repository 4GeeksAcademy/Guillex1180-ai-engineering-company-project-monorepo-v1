import { useEffect, useState } from "react";
import {
  createSupplier,
  getSuppliers,
  updateSupplierRate,
  updateSupplierStatus,
} from "./api";
import { CATEGORY_LABELS } from "./constants";
import { SupplierForm } from "./SupplierForm";
import { SupplierTable } from "./SupplierTable";
import {
  VALID_CATEGORIES,
  type Supplier,
  type SupplierCategory,
  type SupplierCountry,
  type SupplierCreate,
} from "./types";

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [country, setCountry] = useState<SupplierCountry | "">("");
  const [category, setCategory] = useState<SupplierCategory | "">("");
  const [reload, setReload] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    setError(null);

    getSuppliers({ country: country || undefined, category: category || undefined })
      .then((data) => {
        if (active) setSuppliers(data);
      })
      .catch((requestError: unknown) => {
        if (active) setError(errorMessage(requestError, "No se pudo cargar el directorio."));
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [country, category, reload]);

  const replaceSupplier = (updated: Supplier) => {
    setSuppliers((current) => current.map((item) => item.id === updated.id ? updated : item));
  };

  const handleCreate = async (payload: SupplierCreate) => {
    setIsSaving(true);
    setError(null);
    try {
      await createSupplier(payload);
      setIsFormOpen(false);
      setReload((value) => value + 1);
    } catch (requestError) {
      setError(errorMessage(requestError, "No se pudo registrar el proveedor."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleRateUpdate = async (id: number, rate: number): Promise<boolean> => {
    setPendingId(id);
    setError(null);
    try {
      replaceSupplier(await updateSupplierRate(id, rate));
      return true;
    } catch (requestError) {
      setError(errorMessage(requestError, "No se pudo actualizar la tarifa."));
      return false;
    } finally {
      setPendingId(null);
    }
  };

  const handleStatusToggle = async (supplier: Supplier) => {
    setPendingId(supplier.id);
    setError(null);
    try {
      const status = supplier.status === "active" ? "suspended" : "active";
      replaceSupplier(await updateSupplierStatus(supplier.id, status));
    } catch (requestError) {
      setError(errorMessage(requestError, "No se pudo cambiar el estado."));
    } finally {
      setPendingId(null);
    }
  };

  return (
    <main className="directory-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Carrier Operations</p>
          <h1>Directorio de Proveedores</h1>
          <p>Red consolidada de servicios logísticos para USA y España.</p>
        </div>
        <button className="primary-button" type="button" onClick={() => setIsFormOpen(true)}>
          Nuevo proveedor
        </button>
      </header>

      <section className="filters" aria-label="Filtros de proveedores">
        <label>País
          <select value={country} onChange={(event) => setCountry(event.target.value as SupplierCountry | "")}>
            <option value="">Todos</option>
            <option value="USA">USA</option>
            <option value="Spain">Spain</option>
          </select>
        </label>
        <label>Categoría
          <select value={category} onChange={(event) => setCategory(event.target.value as SupplierCategory | "")}>
            <option value="">Todas</option>
            {VALID_CATEGORIES.map((value) => <option key={value} value={value}>{CATEGORY_LABELS[value]}</option>)}
          </select>
        </label>
        <p aria-live="polite">{isLoading ? "Actualizando..." : `${suppliers.length} proveedores`}</p>
      </section>

      {error && !isFormOpen ? <p className="alert" role="alert">{error}</p> : null}
      <SupplierTable
        suppliers={suppliers}
        isLoading={isLoading}
        pendingId={pendingId}
        onRateUpdate={handleRateUpdate}
        onStatusToggle={handleStatusToggle}
      />

      {isFormOpen ? (
        <SupplierForm
          error={error}
          isSaving={isSaving}
          onCancel={() => {
            if (!isSaving) {
              setIsFormOpen(false);
              setError(null);
            }
          }}
          onSubmit={handleCreate}
        />
      ) : null}
    </main>
  );
}