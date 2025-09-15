import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


security = HTTPBearer()


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify the Bearer token against the API_SECRET environment variable
    """
    api_secret = os.getenv("API_SECRET")

    if not api_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_SECRET not configured"
        )

    bearer_token = credentials.credentials

    if not bearer_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No API secret provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if bearer_token != api_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API secret",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials
