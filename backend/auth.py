"""
Verifies the session token issued by NextAuth so protected FastAPI routes know
which user is calling.

IMPORTANT NOTE (read before wiring this into production):
NextAuth's default JWT strategy does NOT produce a plain signed JWT — it
produces an encrypted JWE (A256GCM) derived from NEXTAUTH_SECRET, which
python-jose's `jwt.decode` (HS256) cannot verify as-is. To make this
cross-service verification work, override the `encode`/`decode` functions in
the frontend's NextAuth `jwt` config to emit a standard HS256-signed JWT
instead of the default JWE, e.g.:

    // frontend/pages/api/auth/[...nextauth].ts
    jwt: {
      async encode({ secret, token }) {
        return jwt.sign(token as object, secret as string, { algorithm: "HS256" });
      },
      async decode({ secret, token }) {
        return jwt.verify(token as string, secret as string) as JWT;
      },
    },

Once that's in place, this dependency will correctly verify tokens issued by
the frontend using the same JWT_SECRET / NEXTAUTH_SECRET.
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
    return payload
