import { FormEvent, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { getApiErrorMessage, resetPassword } from "../services/authApi";

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token") ?? "";
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);

    if (!token) {
      setErrorMessage("El enlace de recuperación no contiene un token válido.");
      return;
    }
    if (newPassword !== confirmation) {
      setErrorMessage("Las contraseñas no coinciden.");
      return;
    }

    setIsSubmitting(true);
    try {
      await resetPassword(token, newPassword);
      navigate("/login", {
        replace: true,
        state: { message: "La contraseña se actualizó correctamente." },
      });
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error, "El enlace no es válido o ha expirado."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="reset-password-title">
        <p className="auth-kicker">Cuenta segura</p>
        <h1 id="reset-password-title">Crea una contraseña nueva</h1>
        <p className="auth-intro">Elige una contraseña de al menos 8 caracteres.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="new-password">Nueva contraseña</label>
          <input
            id="new-password"
            type="password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            autoComplete="new-password"
            minLength={8}
            required
            disabled={isSubmitting}
          />

          <label htmlFor="confirm-password">Confirmar nueva contraseña</label>
          <input
            id="confirm-password"
            type="password"
            value={confirmation}
            onChange={(event) => setConfirmation(event.target.value)}
            autoComplete="new-password"
            minLength={8}
            required
            disabled={isSubmitting}
          />

          <button className="action-button auth-submit" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Actualizando..." : "Actualizar contraseña"}
          </button>
        </form>

        {errorMessage ? (
          <p className="error-message" role="alert">
            {errorMessage}
          </p>
        ) : null}

        <Link className="auth-link" to="/forgot-password">
          Solicitar un enlace nuevo
        </Link>
      </section>
    </main>
  );
}
