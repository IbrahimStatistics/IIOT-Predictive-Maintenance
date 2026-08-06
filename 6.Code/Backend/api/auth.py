from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
import secrets

from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_MINUTES

# TEMPORARY: single hardcoded test user, replace with a real users table + RBAC later
FAKE_USER = {"username": "admin", "password": "admin123"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRY_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def authenticate_user(username: str, password: str) -> bool:
    username_ok = secrets.compare_digest(username, FAKE_USER["username"])
    password_ok = secrets.compare_digest(password, FAKE_USER["password"])
    return username_ok and password_ok


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")