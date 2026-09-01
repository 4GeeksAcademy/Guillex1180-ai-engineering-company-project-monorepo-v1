import { useState, type FormEvent } from "react";
import { CATEGORY_LABELS } from "./constants";
import {
  VALID_CATEGORIES,
  type SupplierCategory,
  type SupplierCountry,
  type SupplierCreate,
  type SupplierCurrency,
} from "./types";

interface SupplierFormProps {
  error: string | null;
  isSaving: boolean;
  onCancel: () => void;
  onSubmit: (payload: SupplierCreate) => Promise<void>;
}

interface FormState {
  name: string;
  country: SupplierCountry;
  currency: SupplierCurrency;
  categories: SupplierCategory[];
  rate: string;
  serviceZone: string;
  email: string;
  notes: string;
}

const INITIAL_FORM: FormState = {
  name: "",
  country: "USA",
  currency: "USD",
  categories: [],
  rate: "",
  serviceZone: "",
  email: "",
  notes: "",
};

export function SupplierForm({ error, isSaving, onCancel, onSubmit }: SupplierFormProps) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const rate = Number(form.rate);

    if (!form.name.trim() || form.categories.length === 0 || !Number.isFinite(rate) || rate <= 0) {
      setValidationError("Indica el nombre, al menos una categoría y una tarifa mayor que cero.");
      return;
    }

    setValidationError(null);
    await onSubmit({
      name: form.name.trim(),
      country: form.country,
      currency: form.currency,
      categories: form.categories,
      rate_per_shipment: rate,
      status: "active",
      ...(form.serviceZone.trim() && { service_zone: form.serviceZone.trim() }),
      ...(form.email.trim() && { contact_email: form.email.trim() }),
      ...(form.notes.trim() && { notes: form.notes.trim() }),
    });
  };

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="supplier-modal" role="dialog" aria-modal="true" aria-labelledby="supplier-form-title">
        <header className="modal-header">
          <div>
            <p className="eyebrow">Alta de red</p>
            <h2 id="supplier-form-title">Registrar proveedor</h2>
          </div>
          <button type="button" className="quiet-button" onClick={onCancel} disabled={isSaving}>Cerrar</button>
        </header>

        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <label className="wide-field">Nombre comercial
              <input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
            </label>
            <label>País
              <select value={form.country} onChange={(event) => {
                const country = event.target.value as SupplierCountry;
                setForm({ ...form, country, currency: country === "USA" ? "USD" : "EUR" });
              }}>
                <option value="USA">USA</option>
                <option value="Spain">Spain</option>
              </select>
            </label>
            <label>Moneda
              <select value={form.currency} onChange={(event) => setForm({ ...form, currency: event.target.value as SupplierCurrency })}>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
              </select>
            </label>
            <label>Tarifa por envío
              <input required type="number" min="0.01" step="0.01" value={form.rate} onChange={(event) => setForm({ ...form, rate: event.target.value })} />
            </label>
            <label>Zona de servicio
              <input value={form.serviceZone} onChange={(event) => setForm({ ...form, serviceZone: event.target.value })} />
            </label>

            <fieldset className="category-options wide-field">
              <legend>Categorías</legend>
              <div>
                {VALID_CATEGORIES.map((category) => (
                  <label key={category}>
                    <input
                      type="checkbox"
                      checked={form.categories.includes(category)}
                      onChange={(event) => setForm({
                        ...form,
                        categories: event.target.checked
                          ? [...form.categories, category]
                          : form.categories.filter((value) => value !== category),
                      })}
                    />
                    {CATEGORY_LABELS[category]}
                  </label>
                ))}
              </div>
            </fieldset>

            <label className="wide-field">Email de contacto
              <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            </label>
            <label className="wide-field">Notas
              <textarea rows={3} value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} />
            </label>
          </div>

          {validationError || error ? <p className="alert" role="alert">{validationError ?? error}</p> : null}
          <footer className="modal-actions">
            <button type="button" className="secondary-button" onClick={onCancel} disabled={isSaving}>Cancelar</button>
            <button type="submit" className="primary-button" disabled={isSaving}>
              {isSaving ? "Registrando..." : "Registrar proveedor"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}