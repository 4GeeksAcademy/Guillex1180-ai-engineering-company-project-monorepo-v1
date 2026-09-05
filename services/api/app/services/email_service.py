import os
from html import escape
from pathlib import Path
from urllib.parse import quote

import resend
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / ".env")


def send_reset_password_email(to_email: str, reset_token: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    frontend_url = os.getenv("FRONTEND_URL")

    if not api_key:
        raise RuntimeError("RESEND_API_KEY no está configurada")
    if not frontend_url:
        raise RuntimeError("FRONTEND_URL no está configurada")

    reset_url = (
        f"{frontend_url.rstrip('/')}/reset-password?token={quote(reset_token, safe='')}"
    )
    resend.api_key = api_key

    try:
        resend.Emails.send(
            {
                "from": "onboarding@resend.dev",
                "to": [to_email],
                "subject": "Restablecimiento de Contraseña",
                "html": (
                    "<p>Has solicitado restablecer tu contraseña.</p>"
                    f'<p><a href="{escape(reset_url, quote=True)}">'
                    "Restablecer contraseña</a></p>"
                    "<p>Si no solicitaste este cambio, puedes ignorar este correo.</p>"
                ),
            }
        )
    except Exception as exc:
        raise RuntimeError("No se pudo enviar el correo de restablecimiento") from exc