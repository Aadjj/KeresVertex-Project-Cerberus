from fastapi import Request, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hmac

SHARED_SECRET = "keres_shadow_key_2026"

security = HTTPBearer()

def authenticate_beacon(credentials: HTTPAuthorizationCredentials = Security(security)):
    if not hmac.compare_digest(credentials.credentials, SHARED_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid operational token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True