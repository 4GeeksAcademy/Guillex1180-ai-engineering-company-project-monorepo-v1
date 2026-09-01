import SuppliersPage from "./suppliers/page";

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="brand-mark">TF</p>
          <p className="brand-name">TrackFlow</p>
        </div>
        <nav aria-label="Navegación principal">
          <a className="nav-link active" href="/">Directorio de Proveedores</a>
        </nav>
        <p className="sidebar-meta">Operaciones internas</p>
      </aside>
      <SuppliersPage />
    </div>
  );
}