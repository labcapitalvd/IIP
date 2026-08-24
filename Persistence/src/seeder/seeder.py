import importlib.util
import os

from shared.utils import format_banner, format_list
from shared.utils.logger import configure_logging, getLogger

logger = getLogger(__name__)


def main():
    configure_logging()

    seeds_dir = os.path.join(os.path.dirname(__file__), "seeds")

    logger.info(format_banner("DATABASE SEEDING INITIALIZED"))

    if not os.path.isdir(seeds_dir):
        logger.error(f"Seeds directory not found: {seeds_dir}")
        return

    seed_files = sorted(
        [
            filename[:-3]
            for filename in os.listdir(seeds_dir)
            if filename.endswith(".py") and filename != "__init__.py"
        ]
    )

    successful_seeds: list[str] = []
    failed_seeds: list[str] = []

    for module_name in seed_files:
        file_path = os.path.join(seeds_dir, f"{module_name}.py")
        logger.debug(format_banner(f"Running {module_name}.upgrade()"))

        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.warning(f"Could not load {module_name}.py")
                failed_seeds.append(f"{module_name} (Load Error)")
                continue

            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]

            if hasattr(mod, "upgrade") and callable(mod.upgrade):
                mod.upgrade()
                successful_seeds.append(module_name)
            else:
                logger.warning(f"{module_name} has no callable upgrade()")
                failed_seeds.append(f"{module_name} (No upgrade())")

        except Exception as e:
            logger.error(
                f"Failed to execute {module_name}: {type(e).__name__} - {e}",
                exc_info=True,
            )
            failed_seeds.append(f"{module_name} ({type(e).__name__})")

    # Display accurate execution results
    if successful_seeds:
        logger.info(format_list("Successful Seeds", successful_seeds))

    if failed_seeds:
        logger.error(format_list("Failed Seeds", failed_seeds))

    logger.info(format_banner("SEEDING PROCESS COMPLETE"))


if __name__ == "__main__":
    main()
