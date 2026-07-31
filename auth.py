from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
import httpx
from config import SUPABASE_JWKS_URL


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        # Get the token header so we know which signing key was used
        header = jwt.get_unverified_header(token)

        # Fetch Supabase public keys
        async with httpx.AsyncClient() as client:
            response = await client.get(SUPABASE_JWKS_URL)
            jwks = response.json()

        # Find the matching key
        signing_key = None

        for key in jwks["keys"]:
            if key["kid"] == header["kid"]:
                signing_key = key
                break

        if not signing_key:
            raise Exception("Matching signing key not found")

        # Verify and decode the JWT
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["ES256"],
            options={
                "verify_aud": False,
            },
        )

        return {
            "id": payload["sub"],
            "email": payload.get("email"),
        }

    except Exception as e:
        print("AUTH ERROR:", e)

        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )