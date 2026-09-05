from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Request

if __package__ == "services.api.app.services":
    from ...database import audit_logs
else:
    from database import audit_logs


def record_auth_event(
    user_id: int | None,
    event_type: str,
    request: Request,
) -> None:
    audit_logs.insert(
        {
            "user_id": user_id,
            "event_type": event_type,
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )