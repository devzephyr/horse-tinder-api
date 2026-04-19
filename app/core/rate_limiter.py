from fastapi import Request
from slowapi import Limiter

from app.core.config import settings


def _get_remote_address(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_user_or_ip(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            import jwt

            from app.core.config import settings as app_settings

            token = auth_header.split(" ", 1)[1]
            payload = jwt.decode(
                token, app_settings.ACCESS_TOKEN_SECRET, algorithms=["HS256"]
            )
            return f"user:{payload['sub']}"
        except Exception:
            pass
    return _get_remote_address(request)


limiter = Limiter(
    key_func=_get_user_or_ip,
    storage_uri=settings.RATE_LIMIT_STORAGE_URI,
)
