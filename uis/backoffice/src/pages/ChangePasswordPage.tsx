import { FormEvent, useState } from "react";
import { changePassword, getAccessToken, getApiErrorMessage } from "../services/authApi";

export function ChangePasswordPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage(null);
    setErrorMessage(null);

    if (newPassword !== confirmation) {
      setErrorMessage("Las contraseñas nuevas no coinciden.");
      return;
    }

    const accessToken = getAccessToken();
    if (!accessToken) {
      setErrorMessage("Tu sesión ha caducado. Inicia sesión de nuevo.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await changePassword(currentPassword, newPassword, accessToken);
      setMessage(response.message || "La contraseña se actualizó correctamente.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmation("");
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error, "No se pudo actualizar la contraseña."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-shell">
      <header className="page-header">
        <p className="auth-kicker">Seguridad de la cuenta</p>
        <h1>Cambiar contraseña</h1>
        <p>Actualiza tu contraseña desde tu sesión activa.</p>
      </header>

      <section className="panel password-panel" aria-labelledby="change-password-title">
        <h2 id="change-password-title">Nueva contraseña</h2>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="current-password">Contraseña actual</label>
          <input
            id="current-password"
            type="password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            autoComplete="current-password"
            required
            disabled={isSubmitting}
          />

          <label htmlFor="account-new-password">Nueva contraseña</label>
          <input
            id="account-new-password"
            type="password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            autoComplete="new-password"
            minLength={8}
            required
            disabled={isSubmitting}
          />

          <label htmlFor="account-confirm-password">Confirmar nueva contraseña</label>
          <input
            id="account-confirm-password"
            type="password"
            value={confirmation}
            onChange={(event) => setConfirmation(event.target.value)}
            autoComplete="new-password"
            minLength={8}
            required
            disabled={isSubmitting}
          />

          <button className="action-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Guardando..." : "Guardar contraseña"}
          </button>
        </form>

        {message ? <p className="success-message" role="status">{message}</p> : null}
        {errorMessage ? <p className="error-message" role="alert">{errorMessage}</p> : null}
      </section>
    </div>
  );
}
