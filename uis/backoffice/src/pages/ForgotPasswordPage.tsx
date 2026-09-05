import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { requestPasswordReset } from "../services/authApi";

const confirmationMessage = "Si esa dirección está registrada, recibirás un enlace en breve.";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isSubmitting || hasSubmitted) {
      return;
    }

    setIsSubmitting(true);
    setHasSubmitted(true);
    try {
      await requestPasswordReset(email);
    } catch {
      // Keep the same confirmation to avoid exposing whether the address exists.
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="forgot-password-title">
        <p className="auth-kicker">Cuenta segura</p>
        <h1 id="forgot-password-title">Recupera tu acceso</h1>
        <p className="auth-intro">
          Introduce tu email y te enviaremos un enlace para crear una contraseña nueva.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="forgot-email">Email</label>
          <input
            id="forgot-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
            disabled={isSubmitting || hasSubmitted}
          />
          <button className="action-button auth-submit" type="submit" disabled={isSubmitting || hasSubmitted}>
            {isSubmitting ? "Enviando..." : hasSubmitted ? "Solicitud enviada" : "Enviar enlace"}
          </button>
        </form>

        {hasSubmitted ? (
          <p className="success-message" role="status" aria-live="polite">
            {confirmationMessage}
          </p>
        ) : null}

        <Link className="auth-link" to="/login">
          Volver al inicio de sesión
        </Link>
      </section>
    </main>
  );
}
