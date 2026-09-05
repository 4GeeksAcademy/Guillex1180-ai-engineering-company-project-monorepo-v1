import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { getApiErrorMessage, login, ACCESS_TOKEN_KEY } from "../services/authApi";

type LoginLocationState = {
  message?: string;
};

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LoginLocationState | null;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const response = await login(email, password);
      localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token);
      navigate("/", { replace: true });
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error, "No se pudo iniciar sesión."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="login-title">
        <p className="auth-kicker">TrackFlow Backoffice</p>
        <h1 id="login-title">Inicia sesión</h1>
        <p className="auth-intro">Accede a las herramientas de operaciones de tu equipo.</p>

        {state?.message ? <p className="success-message" role="status">{state.message}</p> : null}

        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="login-email">Email</label>
          <input
            id="login-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
            disabled={isSubmitting}
          />
          <label htmlFor="login-password">Contraseña</label>
          <input
            id="login-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
            disabled={isSubmitting}
          />
          <button className="action-button auth-submit" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Entrando..." : "Iniciar sesión"}
          </button>
        </form>

        {errorMessage ? <p className="error-message" role="alert">{errorMessage}</p> : null}
        <Link className="auth-link" to="/forgot-password">
          ¿Olvidaste tu contraseña?
        </Link>
      </section>
    </main>
  );
}
