"""
Verifies the API bearer token issued by the frontend so protected FastAPI
routes know which user is calling.

NOTE on the earlier approach (kept for history): NextAuth's own session
cookie uses an encrypted JWE by default, which python-jose's HS256 decoder
can't verify as-is, and overriding NextAuth's encode/decode to force HS256
would also change how the session cookie itself is protected. Instead, the
frontend signs a small, separate HS256 token (see
`frontend/pages/api/auth/[...nextauth].ts`, the `apiToken` claim) purely for
calling this backend. It carries only { sub: <internal user id>,
githubUsername }, signed with the same JWT_SECRET / NEXTAUTH_SECRET both
services share.
"""

import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

JWT_SECRET = os.getenv("JWT_SECRET", "generate_a_random_string")
JWT_ALGORITHM = "HS256"

bearer_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
        )
    if "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )
    return payload


def require_matching_user_id(user_id: int, current_user: dict = Depends(get_current_user)) -> dict:
    """
    Use as a dependency on routes that take a `user_id` in the request body:
    raises 403 if the authenticated token's subject doesn't match the
    user_id the caller is claiming to act as.
    """
    try:
        token_user_id = int(current_user["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    if token_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token does not authorize acting as this user_id",
        )
    return current_user
