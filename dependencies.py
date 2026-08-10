import os

from secrets import compare_digest

from dotenv import load_dotenv

from fastapi import (
    Request,
    HTTPException,
    status,
    Header
)

from jwt import verify_access_token


load_dotenv()


API_KEY = os.getenv("API_KEY")


def get_current_user(
    request: Request,
    x_api_key: str | None = Header(
        default=None,
        alias="X-API-Key"
    )
):

    # =================================================
    # 1. API KEY AUTHENTICATION
    # =================================================

    if not x_api_key:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key is required"
        )

    if not API_KEY or not compare_digest(
        x_api_key,
        API_KEY
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )


    # =================================================
    # 2. JWT AUTHENTICATION
    # =================================================

    token = request.cookies.get(
        "access_token"
    )

    if not token:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )


    # =================================================
    # 3. VERIFY JWT
    # =================================================

    payload = verify_access_token(
        token
    )

    if payload is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


    # =================================================
    # 4. GET USER ID
    # =================================================

    user_id = payload.get("sub")

    if user_id is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )


    return int(user_id)