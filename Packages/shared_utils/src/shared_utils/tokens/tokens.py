import os
from datetime import datetime, timedelta, timezone
from typing import Literal, Annotated
from uuid import UUID
from uuid_utils import uuid7

from fastapi import Request, Response, Header, HTTPException, Cookie, Body, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from joserfc import jwt
from joserfc.errors import (
    BadSignatureError,
    ConflictAlgorithmError,
    DecodeError,
    ExceededSizeError,
    ExpiredTokenError,
    InsecureClaimError,
    InvalidExchangeKeyError,
    JoseError,
)

from shared_schemas import ResponseAuth

from .config import (
    JWT_EXPIRE_MINUTES_ACCESS,
    JWT_EXPIRE_MINUTES_REFRESH,
    PRIVATE_KEY,
    PUBLIC_KEY,
    REGISTRY,
)

from .errors import (
    TokenEncodeError,
    TokenDecodeError,
    TokenExpiredError,
    TokenSignatureError,
    TokenEmptyError,
    TokenTypeError,
    InvalidPlatformError,
)


PRODUCTION_MODE = os.getenv("PRODUCTION_MODE", "false").lower() in ("1", "true", "yes")

COOKIES_SECURE = False if not PRODUCTION_MODE else True
COOKIES_SAMESITE = "strict" if PRODUCTION_MODE and COOKIES_SECURE else "lax"

security = HTTPBearer(auto_error=False)

TokenType = Literal["access", "refresh"]


def generate_token(
    user_id: UUID, username: str, token_type: TokenType = "access"
) -> tuple[str, int, UUID | None]:
    """
    Generate either an access or refresh token.
    token_type: "access" | "refresh"
    """
    try:
        now = datetime.now(timezone.utc)

        expire_minutes = (
            JWT_EXPIRE_MINUTES_ACCESS
            if token_type == "access"
            else JWT_EXPIRE_MINUTES_REFRESH
        )
        exp = now + timedelta(minutes=expire_minutes)

        header = {"typ": "JWT", "alg": "EdDSA"}

        claims = {
            "sub": str(user_id),
            "username": str(username),
            "token_type": str(token_type),
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }

        jti = None
        if token_type == "refresh":
            jti = str(uuid7())
            claims["jti"]: UUID = jti

        token = jwt.encode(header, claims, PRIVATE_KEY, registry=REGISTRY)
        return token, int(exp.timestamp()), UUID(jti)

    except InsecureClaimError as e:
        raise TokenEncodeError("Insecure claim error") from e

    except JoseError as e:
        raise TokenEncodeError(f"Error encoding {token_type} token") from e


def decode_token(token: str, expected_type: TokenType):
    """
    Decode a JWT and validate its type.
    expected_type: "access" | "refresh"
    """
    try:
        payload = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["EdDSA"],
        )

        if payload.claims.get("token_type") != expected_type:
            raise TokenTypeError(f"Token must be a {expected_type} token")

        return payload

    except BadSignatureError:
        raise TokenSignatureError("Invalid token signature")

    except ConflictAlgorithmError:
        raise TokenDecodeError("Invalid token algorithm")

    except DecodeError:
        raise TokenDecodeError("Invalid token")

    except ExpiredTokenError:
        raise TokenExpiredError(f"{expected_type.capitalize()} token expired")

    except ExceededSizeError:
        raise TokenDecodeError("Token exceeded size limit")

    except InvalidExchangeKeyError:
        raise TokenDecodeError("Invalid exchange key")

    except JoseError as e:
        raise TokenDecodeError(f"Error decoding {expected_type} token") from e


class AccessContext:
    def __init__(
        self,
        request: Request,
        response: Response,
        platform: Annotated[str, Header(alias="X-Platform")] = "web",
        access_token: Annotated[
            HTTPAuthorizationCredentials | None, Depends(security)
        ] = None,
    ):
        self.request = request
        self.response = response
        self.platform = platform
        # Store with a different name to avoid property collision
        self._raw_token = access_token

        # Your smart browser-spoofing check
        if self.platform == "mobile" and (
            request.headers.get("origin") or request.headers.get("referer")
        ):
            raise InvalidPlatformError("Browsers cannot claim to be mobile.")

    @property
    def access_token(self) -> str:
        if not self._raw_token or not self._raw_token.credentials:
            raise TokenEmptyError("Missing token in Authorization header")
        return self._raw_token.credentials


class SessionContext:
    def __init__(
        self,
        request: Request,
        response: Response,
        platform: Annotated[str, Header(alias="X-Platform")] = "web",
        cookie_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
        header_token: Annotated[str | None, Header(alias="X-Refresh-Token")] = None,
    ):
        self.request = request
        self.response = response
        self.platform = platform
        self._cookie_token = cookie_token
        self._header_token = header_token

        if self.platform == "mobile":
            origin = request.headers.get("origin")
            referer = request.headers.get("referer")
            if origin or referer:
                raise InvalidPlatformError(
                    "Browsers cannot claim to be mobile to bypass cookie security."
                )

    @property
    def refresh_token(self) -> str:
        """
        Logic-based extraction of the refresh token.
        """
        if self.platform == "web":
            if not self._cookie_token:
                raise TokenEmptyError("Missing refresh token in cookies")
            return self._cookie_token

        if self.platform == "mobile":
            if not self._header_token:
                raise TokenEmptyError("Missing refresh token in X-Refresh-Token header")
            # No .credentials needed here because it's a custom header string
            return self._header_token

        raise InvalidPlatformError(f"Unknown platform: {self.platform}")

    def _set_refresh_cookie(self, refresh_token: str):
        if self.platform == "web":
            self.response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=COOKIES_SECURE,
                samesite=COOKIES_SAMESITE,
                max_age=(JWT_EXPIRE_MINUTES_REFRESH * 60) - 120,
                path="/auth",
            )

    def unset_refresh_cookie(self):
        if self.platform == "web":
            self.response.delete_cookie(
                key="refresh_token",
                httponly=True,
                secure=COOKIES_SECURE,
                samesite=COOKIES_SAMESITE,
                path="/auth",
            )

    def make_response(self, access_token: str, refresh_token: str) -> ResponseAuth:
        """
        Constructs the appropriate response structure and sets cookies if
        needed.
        """
        if self.platform == "web":
            self._set_refresh_cookie(refresh_token)
            return ResponseAuth(
                access_token=access_token,
                refresh_token=None,
                message="Auth successful (web)",
            )

        return ResponseAuth(
            access_token=access_token,
            refresh_token=refresh_token,
            message="Auth successful (mobile)",
        )
