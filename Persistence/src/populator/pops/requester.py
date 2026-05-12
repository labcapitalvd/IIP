import os
import requests
from typing import Any
from shared_utils.logger import get_logger

logger = get_logger(__name__)

class GitHubConnector:
    def __init__(self, token_secret_path: str = "/run/secrets/github_token_seeds"):
        self.token_path = token_secret_path
        self._token = self._load_token()
        self.headers = {
            "Authorization": f"token {self._token}",
            "Accept": "application/vnd.github.v3.raw",
        }

    def _load_token(self) -> str:
        if not os.path.exists(self.token_path):
            logger.critical("GitHub token missing at %s", self.token_path)
            raise FileNotFoundError(f"Secret not found: {self.token_path}")
        
        with open(self.token_path, "r") as f:
            return f.read().strip()

    def get_json(self, url: str) -> Any:
        """Fetch and parse JSON from a GitHub URL."""
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_raw_text(self, url: str) -> str:
        """Fetch raw content (CSV, text, etc.) from a GitHub URL."""
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.text
