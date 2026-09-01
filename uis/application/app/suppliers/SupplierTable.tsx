import { useState } from "react";
import { CATEGORY_LABELS } from "./constants";
import type { Supplier } from "./types";

interface SupplierTableProps {
  isLoading: boolean;
  pendingId: number | null;
  suppliers: Supplier[];
  onRateUpdate: (id: number, rate: number) => Promise<boolean>;
  onStatusToggle: (supplier: Supplier) => Promise<void>;
}

function formatRate(supplier: Supplier): string {
  return new Intl.NumberFormat(supplier.country === "USA" ? "en-US" : "es-ES", {
    style: "currency",
    currency: supplier.currency,
  }).format(supplier.rate_per_shipment);
}

function formatDate(timestamp: string): string {
  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(timestamp));
}

export function SupplierTable({
  isLoading,
  pendingId,
  suppliers,
  onRateUpdate,
  onStatusToggle,
}: SupplierTableProps) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [rateDraft, setRateDraft] = useState("");
  const [rateError, setRateError] = useState<string | null>(null);

  const saveRate = async (id: number) => {
    const rate = Number(rateDraft);
    if (!Number.isFinite(rate) || rate <= 0) {
      setRateError("La tarifa debe ser mayor que cero.");
      return;
    }

    setRateError(null);
    if (await onRateUpdate(id, rate)) {
      setEditingId(null);
      setRateDraft("");
    }
  };

  return (
    <section className="table-frame" aria-busy={isLoading}>
      {rateError ? <p className="inline-alert" role="alert">{rateError}</p> : null}
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Proveedor</th>
              <th>País</th>
              <th>Categorías</th>
              <th>Tarifa por envío</th>
              <th>Estado</th>
              <th>Actualización</th>
              <th><span className="sr-only">Acciones</span></th>
            </tr>
          </thead>
          <tbody>
            {!isLoading && suppliers.length === 0 ? (
              <tr><td className="empty-state" colSpan={7}>No hay proveedores para estos filtros.</td></tr>
            ) : null}
            {suppliers.map((supplier) => (
              <tr key={supplier.id}>
                <td>
                  <strong>{supplier.name}</strong>
                  {supplier.service_zone ? <small>{supplier.service_zone}</small> : null}
                </td>
                <td className="country">{supplier.country}</td>
                <td>
                  <div className="badges">
                    {supplier.categories.map((category) => (
                      <span className="category-badge" key={category}>{CATEGORY_LABELS[category]}</span>
                    ))}
                  </div>
                </td>
                <td>
                  {editingId === supplier.id ? (
                    <div className="rate-editor">
                      <input
                        aria-label={`Nueva tarifa para ${supplier.name}`}
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={rateDraft}
                        onChange={(event) => setRateDraft(event.target.value)}
                      />
                      <button type="button" onClick={() => saveRate(supplier.id)} disabled={pendingId === supplier.id}>Guardar</button>
                      <button type="button" className="quiet-button" onClick={() => setEditingId(null)}>Cancelar</button>
                    </div>
                  ) : (
                    <button type="button" className="rate-link" onClick={() => {
                      setEditingId(supplier.id);
                      setRateDraft(String(supplier.rate_per_shipment));
                    }}>
                      {formatRate(supplier)}
                    </button>
                  )}
                </td>
                <td>
                  <span className={`status status-${supplier.status}`}>
                    {supplier.status === "active" ? "Activo" : "Suspendido"}
                  </span>
                </td>
                <td><time dateTime={supplier.updated_at}>{formatDate(supplier.updated_at)}</time></td>
                <td>
                  <button
                    type="button"
                    className="status-button"
                    disabled={pendingId === supplier.id}
                    onClick={() => onStatusToggle(supplier)}
                  >
                    {supplier.status === "active" ? "Suspender" : "Activar"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}