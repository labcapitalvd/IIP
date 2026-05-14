import importlib.util
import os
import traceback
import asyncio

from shared_utils.logger import get_logger
from .connectors import GitHubConnector, ServiceClient

logger = get_logger("pop/tables")

# Load configuration from environment
AUTH_HOST = os.environ.get("AUTH_HOST", "localhost")
AUTH_PORT = int(os.environ.get("AUTH_PORT", 4293))

CORE_HOST = os.environ.get("CORE_HOST", "localhost")
CORE_PORT = int(os.environ.get("CORE_PORT", 4294))

SEED_USER = os.environ["SEED_USER"]
SEED_PWD = os.environ["SEED_PWD"]


async def run_populators():
    pops_dir = os.path.join(os.path.dirname(__file__), "pops")

    if not os.path.isdir(pops_dir):
        logger.error(f"pops directory not found: {pops_dir}")
        return

    # 1. Initialize and Auth Connectors once
    gh = GitHubConnector()
    api = ServiceClient(
        core_host=CORE_HOST, 
        core_port=CORE_PORT, 
        auth_host=AUTH_HOST, 
        auth_port=AUTH_PORT
    )

    logger.info(f"Authenticating ServiceClient for seeding...")
    if not await api.login(SEED_USER, SEED_PWD):
        logger.critical("Seeding aborted: Could not authenticate with API.")
        return

    logger.info(f"Running pops from {os.path.relpath(pops_dir)}")

    # 2. Iterate through files (sorted handles dependency order if you prefix with numbers like 01_actors.py)
    for filename in sorted(os.listdir(pops_dir)):
        if not filename.endswith(".py") or filename == "__init__.py":
            continue

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
                logger.info(f"--- Executing: {module_name}.upgrade() ---")

                # Check if the module is async (which it should be now)
                if asyncio.iscoroutinefunction(mod.upgrade):
                    await mod.upgrade(gh=gh, api=api)
                else:
                    # Fallback for sync modules if you haven't converted them all yet
                    mod.upgrade(gh=gh, api=api)
            else:
                logger.warning(f"{module_name} has no callable upgrade()")

        except Exception as e:
            logger.error(f"Error in {module_name}: {type(e).__name__} - {e}")
            traceback.print_exc()

    logger.info("Popping process finished successfully.")


if __name__ == "__main__":
    asyncio.run(run_populators())
