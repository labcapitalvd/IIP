import os
import httpx
from typing import Type, TypeVar, List, Any, Optional
from pydantic import BaseModel
from shared_utils.logger import get_logger


logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class GitHubConnector:
    """Handles fetching seed data from GitHub using Docker Secrets for Auth."""

    def __init__(self, token_secret_path: str = "/run/secrets/github_token_seeds"):
        self.token_path = token_secret_path
        self.headers = {
            "Authorization": f"token {self._load_token()}",
            "Accept": "application/vnd.github.v3.raw",
        }

    def _load_token(self) -> str:
        if not os.path.exists(self.token_path):
            logger.critical("GitHub token missing at %s", self.token_path)
            raise FileNotFoundError(f"Secret not found: {self.token_path}")
        with open(self.token_path, "r") as f:
            return f.read().strip()

    async def get_json(self, url: str) -> Any:
        """Fetch and parse JSON from a GitHub URL."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_raw_text(self, url: str) -> str:
        """Fetch raw content (CSV, text, etc.) from a GitHub URL."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text


class ServiceClient:
    """Internal API client to seed data through split FastAPI endpoints."""

    def __init__(self, core_host: str, core_port: int, auth_host: str, auth_port: int):
        self.core_url = f"http://{core_host}:{core_port}".rstrip("/")
        self.auth_url = f"http://{auth_host}:{auth_port}".rstrip("/")
        self.headers = {}
        # Keep track of credentials for auto-reauth if a token expires mid-run
        self._credentials = None

    async def login(self, username: str, password: str) -> bool:
        """Authenticate against the Auth container."""
        self._credentials = {"username": username, "password": password}
        login_url = f"{self.auth_url}/auth/login"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(login_url, json=self._credentials)
                if response.status_code == 200:
                    token = response.json().get("access_token")
                    if token:
                        self.headers["Authorization"] = f"Bearer {token}"
                        logger.info(f"Authenticated successfully at {self.auth_url}")
                        return True

                logger.error(
                    f"Auth failed at {login_url}: {response.status_code} - {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Connection error to Auth service: {e}")
            return False

    async def _verify_auth_or_refresh(self, client: httpx.AsyncClient) -> bool:
        """Helper to check if authorized, attempts auto-refresh if credentials exist."""
        if "Authorization" in self.headers:
            return True
        if self._credentials:
            logger.info(
                "Token missing or cleared. Attempting automatic re-authentication..."
            )
            return await self.login(
                self._credentials["username"], self._credentials["password"]
            )
        return False

    async def create_entry(self, endpoint: str, schema: Type[T], data: dict) -> bool:
        """Validates against shared_schemas and POSTs to the API."""
        try:
            validated_data = schema(**data)
            async with httpx.AsyncClient() as client:
                if not await self._verify_auth_or_refresh(client):
                    logger.error(
                        f"Unauthorized: No valid credentials to target {endpoint}"
                    )
                    return False

                response = await client.post(
                    f"{self.core_url}/{endpoint.lstrip('/')}",
                    json=validated_data.model_dump(mode="json"),
                    headers=self.headers,
                )

                if response.status_code in (200, 201):
                    return True

                # If token expired during long-running tasks, clear and try once more
                if response.status_code == 401 and self._credentials:
                    self.headers.pop("Authorization", None)
                    if await self._verify_auth_or_refresh(client):
                        # Retry request with new token
                        response = await client.post(
                            f"{self.core_url}/{endpoint.lstrip('/')}",
                            json=validated_data.model_dump(mode="json"),
                            headers=self.headers,
                        )
                        if response.status_code in (200, 201):
                            return True

                logger.error(
                    f"API Error [{endpoint}]: {response.status_code} - {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Validation/Connection Error for {endpoint}: {e}")
            return False

    async def create_multiple_entries(
        self, endpoint: str, schema: Type[T], data_list: list[dict]
    ):
        """POSTs a batch of entries utilizing a single client connection pool."""
        success_count = 0
        target_url = f"{self.core_url}/{endpoint.lstrip('/')}"

        async with httpx.AsyncClient() as client:
            if not await self._verify_auth_or_refresh(client):
                logger.error(f"Batch canceled for {endpoint}: Client is unauthorized.")
                return

            for item in data_list:
                try:
                    validated_data = schema(**item)
                    resp = await client.post(
                        target_url,
                        json=validated_data.model_dump(mode="json"),
                        headers=self.headers,
                    )

                    # Handle token expiration mid-loop
                    if resp.status_code == 401 and self._credentials:
                        self.headers.pop("Authorization", None)
                        if await self._verify_auth_or_refresh(client):
                            resp = await client.post(
                                target_url,
                                json=validated_data.model_dump(mode="json"),
                                headers=self.headers,
                            )

                    if resp.status_code in (200, 201):
                        success_count += 1
                    else:
                        logger.warning(
                            f"Row reject on {endpoint}: {resp.status_code} - {resp.text}"
                        )
                except Exception as e:
                    logger.warning(f"Failed row formatting in {endpoint}: {e}")

        logger.info(
            f"Successfully seeded {success_count}/{len(data_list)} for {endpoint}"
        )

    async def get_entries(self, endpoint: str) -> List[dict]:
        """Generic GET handler to check for existing data or lookups."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.core_url}/{endpoint.lstrip('/')}", headers=self.headers
            )
            response.raise_for_status()
            return response.json()
