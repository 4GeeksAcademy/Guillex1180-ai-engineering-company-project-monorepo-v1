import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { IncidentAnalysisPage } from "./pages/IncidentAnalysisPage";
import { ChangePasswordPage } from "./pages/ChangePasswordPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { LoginPage } from "./pages/LoginPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { getAccessToken } from "./services/authApi";

function HomePage() {
  return (
    <section className="panel">
      <h1>Inicio</h1>
      <p>Selecciona una opción del menú para comenzar.</p>
    </section>
  );
}

export default function App() {
  const location = useLocation();
  const isPublicAuthPage = ["/login", "/forgot-password", "/reset-password"].includes(
    location.pathname,
  );

  if (isPublicAuthPage) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/incidents/analyze" element={<IncidentAnalysisPage />} />
          <Route
            path="/account/change-password"
            element={
              getAccessToken() ? (
                <ChangePasswordPage />
              ) : (
                <Navigate to="/login" replace state={{ message: "Inicia sesión para continuar." }} />
              )
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
