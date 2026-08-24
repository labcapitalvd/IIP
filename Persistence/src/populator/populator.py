import asyncio
import importlib.util
import os
import tomllib
import traceback
from typing import Any, List, Type, TypeVar

import httpx
from pydantic import BaseModel
from shared.utils import format_banner, format_list
from shared.utils.logger import configure_logging, getLogger

logger = getLogger(__name__)

# Load configuration from environment

USERS_FILE = "/run/secrets/users_file"
if not os.path.exists(USERS_FILE):
    raise FileNotFoundError(f"USERS_FILE file not found at {USERS_FILE}")
with open(USERS_FILE, "rb") as f:
    users_toml = tomllib.load(f)

user_list = users_toml.get("users", [])

root_user = next((u for u in user_list if u.get("tier") == "root"), None)

if root_user:
    SEED_USER: str = root_user["username"]
    SEED_PASS: str = root_user["password"]
    logger.info(f"Using 'root' tier account: {SEED_USER}")
elif user_list:
    SEED_USER: str = user_list[0]["username"]
    SEED_PASS: str = user_list[0]["password"]
    logger.warning(f"No 'root' tier user found, falling back to: {SEED_USER}")
else:
    logger.critical("Seeding aborted: No users found in USERS_FILE.")
    raise ValueError("No credentials available for seeding.")

T = TypeVar("T", bound=BaseModel)


async def run_populators():
    configure_logging()

    pops_dir = os.path.join(os.path.dirname(__file__), "pops")

    if not os.path.isdir(pops_dir):
        logger.error(f"pops directory not found: {pops_dir}")
        return

    logger.info(format_banner("DATABASE POPULATION"))

    pop_files = [
        f
        for f in sorted(os.listdir(pops_dir))
        if f.endswith(".py") and f != "__init__.py"
    ]

    logger.info(format_list("Files to populate", pop_files))

    # 2. Iterate through files
    for filename in pop_files:
        module_name = filename[:-3]
        file_path = os.path.join(pops_dir, filename)

        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.warning(f"Could not load {filename}")
                continue

            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            # 3. Check for the upgrade function
            if hasattr(mod, "upgrade") and callable(mod.upgrade):
                logger.debug(format_banner(f"Executing: {module_name}.upgrade()"))

                # Check if the module is async
                if asyncio.iscoroutinefunction(mod.upgrade):
                    await mod.upgrade()
                else:
                    # Fallback for sync modules
                    mod.upgrade()
            else:
                logger.warning(f"{module_name} has no callable upgrade()")

        except Exception as e:
            logger.error(f"Error in {module_name}: {type(e).__name__} - {e}")
            traceback.format_exc()

    logger.info(format_banner("POPULATING PROCESS COMPLETE"))


if __name__ == "__main__":
    asyncio.run(run_populators())
