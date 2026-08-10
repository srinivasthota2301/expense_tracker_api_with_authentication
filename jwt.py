from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

import os

from dotenv import load_dotenv


load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")

# Separate secret for refresh tokens. Falls back to a derived value only so
# local dev doesn't break if you forget to set it — set REFRESH_SECRET_KEY
# explicitly in .env for anything beyond local testing.
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY") or f"{SECRET_KEY}_refresh"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30

REFRESH_TOKEN_EXPIRE_DAYS = 7

RESET_TOKEN_EXPIRE_MINUTES = 15


# =====================================================
# ACCESS TOKEN
# =====================================================

def create_access_token(data: dict):

    to_encode = data.copy()

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    to_encode.update({
        "exp": expire,
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def verify_access_token(token: str):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        # Reject a refresh token presented where an access token is expected
        if payload.get("type") != "access":

            return None

        return payload

    except JWTError:

        return None


# =====================================================
# REFRESH TOKEN
# =====================================================

def create_refresh_token(data: dict):

    to_encode = data.copy()

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS
        )
    )

    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        REFRESH_SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def verify_refresh_token(token: str):

    try:

        payload = jwt.decode(
            token,
            REFRESH_SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        # Reject an access token presented where a refresh token is expected
        if payload.get("type") != "refresh":

            return None

        return payload

    except JWTError:

        return None


# =====================================================
# PASSWORD RESET TOKEN
# =====================================================
# Signed with the main SECRET_KEY but distinguished by "type" so it
# can never be swapped in for an access or refresh token. Short-lived
# on purpose — this token grants a password change if intercepted.

def create_reset_token(data: dict):

    to_encode = data.copy()

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=RESET_TOKEN_EXPIRE_MINUTES
        )
    )

    to_encode.update({
        "exp": expire,
        "type": "reset"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def verify_reset_token(token: str):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        if payload.get("type") != "reset":

            return None

        return payload

    except JWTError:

        return None