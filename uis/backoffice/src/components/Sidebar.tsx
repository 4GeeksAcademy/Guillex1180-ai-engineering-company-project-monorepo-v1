import { NavLink } from "react-router-dom";

export function Sidebar() {
  return (
    <aside className="sidebar" aria-label="Navegación principal">
      <h1 className="brand">TrackFlow Backoffice</h1>
      <nav>
        <ul className="menu-list">
          <li>
            <NavLink className="menu-link" to="/">
              Inicio
            </NavLink>
          </li>
          <li>
            <NavLink className="menu-link" to="/incidents/analyze">
              Análisis de incidencias
            </NavLink>
          </li>
        </ul>
      </nav>
    </aside>
  );
}
