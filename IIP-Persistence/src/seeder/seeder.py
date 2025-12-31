import importlib.util
import os
import traceback

from shared_utils.logger import get_logger


logger = get_logger("seed/tables")



def main():
    seeds_dir = os.path.join(os.path.dirname(__file__), "seeds")

    if not os.path.isdir(seeds_dir):
        logger.error(f"Seeds directory not found: {seeds_dir}")
        return

    logger.info(f"Running seeds from {os.path.relpath(seeds_dir)}")

    for filename in sorted(os.listdir(seeds_dir)):
        if not filename.endswith(".py") or filename == "__init__.py":
            continue

        module_name = filename[:-3]
        file_path = os.path.join(seeds_dir, filename)
        logger.info(f"Running {module_name}.upgrade()")

        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.warning(f"Could not load {filename}")
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


if __name__ == "__main__":
    main()
