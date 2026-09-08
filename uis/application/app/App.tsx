import { useState } from "react";
import SuppliersPage from "./suppliers/page";
import IncidentsPage from "./incidents/page";

export default function App() {
  const [activeTab, setActiveTab] = useState<"suppliers" | "incidents">("incidents");

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="brand-mark">TF</p>
          <p className="brand-name">TrackFlow</p>
        </div>
        <nav aria-label="Navegación principal">
          <a
            className={`nav-link${activeTab === "incidents" ? " active" : ""}`}
            href="#"
            onClick={(e) => { e.preventDefault(); setActiveTab("incidents"); }}
          >
            Gestor de Incidencias
          </a>
          <a
            className={`nav-link${activeTab === "suppliers" ? " active" : ""}`}
            href="#"
            onClick={(e) => { e.preventDefault(); setActiveTab("suppliers"); }}
          >
            Directorio de Proveedores
          </a>
        </nav>
        <p className="sidebar-meta">Operaciones internas</p>
      </aside>
      {activeTab === "incidents" ? <IncidentsPage /> : <SuppliersPage />}
    </div>
  );
}