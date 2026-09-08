import { useState } from "react";
import { CATEGORY_OPTIONS, BRANCH_OPTIONS, ORIGIN_LABELS } from "./constants";
import type { IncidentCreate, IncidentOrigin } from "./types";

interface IncidentFormProps {
  onSave: (payload: IncidentCreate) => Promise<void>;
  isSaving: boolean;
}

export function IncidentForm({ onSave, isSaving }: IncidentFormProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<string>(CATEGORY_OPTIONS[0].value);
  const [origin, setOrigin] = useState<IncidentOrigin>("customer");
  const [branch, setBranch] = useState<string>(BRANCH_OPTIONS[0].value);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave({ title, description, category, origin, branch });
    setTitle("");
    setDescription("");
    setCategory(CATEGORY_OPTIONS[0].value);
    setOrigin("customer");
    setBranch(BRANCH_OPTIONS[0].value);
  };

  return (
    <form className="incident-form" onSubmit={handleSubmit}>
      <div className="form-row">
        <label>
          Título <span className="required">*</span>
          <input
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Ej: Paquete perdido en tránsito"
          />
        </label>
        <label>
          Categoría <span className="required">*</span>
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            {CATEGORY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="form-row">
        <label>
          Origen <span className="required">*</span>
          <select value={origin} onChange={(e) => setOrigin(e.target.value as IncidentOrigin)}>
            {(Object.entries(ORIGIN_LABELS) as [IncidentOrigin, string][]).map(([val, label]) => (
              <option key={val} value={val}>{label}</option>
            ))}
          </select>
        </label>
        <label>
          Sede <span className="required">*</span>
          <select value={branch} onChange={(e) => setBranch(e.target.value)}>
            {BRANCH_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>
      </div>
      <label>
        Descripción <span className="required">*</span>
        <textarea
          required
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe el incidente con detalle..."
        />
      </label>
      <div className="form-actions">
        <button type="submit" className="btn-primary" disabled={isSaving}>
          {isSaving ? "Guardando…" : "Registrar incidente"}
        </button>
      </div>
    </form>
  );
}