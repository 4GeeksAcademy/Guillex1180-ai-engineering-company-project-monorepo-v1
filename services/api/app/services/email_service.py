import os
from html import escape
from pathlib import Path
from urllib.parse import quote

import resend
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / ".env")
resend.api_key = os.getenv("RESEND_API_KEY")


def send_reset_password_email(to_email: str, reset_token: str):
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    reset_url = (
        f"{frontend_url.rstrip('/')}/reset-password?token={quote(reset_token, safe='')}"
    )

    try:
        response = resend.Emails.send(
            {
                "from": os.getenv("EMAIL_FROM", "onboarding@resend.dev"),
                "to": to_email,
                "subject": "Restablecer contraseña",
                "html": (
                    '<div style="margin:0; padding:24px 12px; background:#f4f7fb; '
                    'font-family:Arial,sans-serif; color:#1f2937;">'
                    '<div style="box-sizing:border-box; width:100%; max-width:560px; '
                    'margin:0 auto; padding:32px 24px; background:#ffffff;">'
                    '<h2 style="margin:0 0 16px; font-size:24px; line-height:1.25;">'
                    "Recuperación de contraseña</h2>"
                    '<p style="margin:0 0 24px; font-size:16px; line-height:1.5;">'
                    "Has solicitado restablecer tu contraseña. "
                    "Haz clic en el siguiente enlace para continuar.</p>"
                    f'<p style="margin:0 0 24px;"><a href="{escape(reset_url, quote=True)}" '
                    'style="display:inline-block; padding:14px 20px; background:#2563eb; '
                    'color:#ffffff; text-decoration:none; font-size:16px; line-height:1.2; '
                    'border-radius:6px;">Restablecer mi contraseña</a></p>'
                    '<p style="margin:0; font-size:13px; line-height:1.5; color:#6b7280;">'
                    "Este enlace expirará en poco tiempo. Si no solicitaste este cambio, "
                    "puedes ignorar este mensaje.</p>"
                    "</div></div>"
                ),
            }
        )
        return response
    except Exception as exc:
        print(f"Error al enviar el correo con Resend: {exc}")
        return None