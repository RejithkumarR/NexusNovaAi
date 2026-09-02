from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from fastapi import HTTPException

from nova.config import get_settings


def issue_token(username: str) -> str:
    settings = get_settings()
    payload = {"sub": username, "exp": int(time.time()) + settings.auth_token_ttl_minutes * 60}
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(settings.auth_secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{signature}"


def verify_token(token: str | None) -> str:
    if not token or "." not in token:
        raise HTTPException(status_code=401, detail="Authentication required")
    raw, signature = token.rsplit(".", 1)
    expected = hmac.new(get_settings().auth_secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    try:
        padded = raw + "=" * (-len(raw) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc
    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=401, detail="Authentication token expired")
    return str(payload["sub"])
