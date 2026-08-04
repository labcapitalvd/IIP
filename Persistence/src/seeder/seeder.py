import importlib.util
import os
import traceback

from shared.utils import print_list, print_banner
from shared.utils.logger import get_logger, configure_logging

logger = get_logger("seed/tables")


def main():
    configure_logging()

    seeds_dir = os.path.join(os.path.dirname(__file__), "seeds")

    print_banner(
        "DATABASE SEEDER INITIALIZED\nExecuting modular lookup and role migrations.",
        border_char="=",
        padding_x=4,
        padding_y=1,
    )

    if not os.path.isdir(seeds_dir):
        logger.error(f"Seeds directory not found: {seeds_dir}")
        return

    logger.info(f"Running seeds from {os.path.relpath(seeds_dir)}")

    # Collect valid seed modules first for the summary list
    seed_files = sorted(
        [
            filename[:-3]
            for filename in os.listdir(seeds_dir)
            if filename.endswith(".py") and filename != "__init__.py"
        ]
    )

    for module_name in seed_files:
        file_path = os.path.join(seeds_dir, f"{module_name}.py")
        logger.info(f"Running {module_name}.upgrade()")

        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.warning(f"Could not load {module_name}.py")
                continue

            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]

            if hasattr(mod, "upgrade") and callable(mod.upgrade):
                mod.upgrade()
            else:
                logger.warning(f"{module_name} has no callable upgrade()")

        except Exception as e:
            logger.error(f"Error in {module_name}: {type(e).__name__} - {e}")
            traceback.print_exc()

    logger.info("Seeding process finished.")

    # Use print_list to cleanly display executed seed modules in columns
    print_list("Executed Seed Modules", seed_files, cols=3, border_char="─")

    print_banner(
        "SEEDING PROCESS COMPLETE",
        border_char="─",
        padding_x=6,
        padding_y=0,
    )


if __name__ == "__main__":
    main()
