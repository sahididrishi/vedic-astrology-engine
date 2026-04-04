import hmac

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

bearer = HTTPBearer()


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(bearer),
) -> str:
    settings = get_settings()
    token = credentials.credentials
    if not hmac.compare_digest(token, settings.API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token
