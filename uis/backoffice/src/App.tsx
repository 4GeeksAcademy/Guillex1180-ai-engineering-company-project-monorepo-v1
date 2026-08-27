import { Navigate, Route, Routes } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { IncidentAnalysisPage } from "./pages/IncidentAnalysisPage";

function HomePage() {
  return (
    <section className="panel">
      <h1>Inicio</h1>
      <p>Selecciona una opción del menú para comenzar.</p>
    </section>
  );
}

export default function App() {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/incidents/analyze" element={<IncidentAnalysisPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
