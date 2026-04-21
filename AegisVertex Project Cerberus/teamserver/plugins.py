import os
import importlib.util
import logging
import asyncio
from typing import Any

logger = logging.getLogger("Keres.Plugins")


def register(client):

    plugins_dir = os.path.join(os.path.dirname(__file__), "enabled_plugins")

    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir, exist_ok=True)
        logger.info(f"Created plugins directory at {plugins_dir}")
        return

    for filename in os.listdir(plugins_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            plugin_name = filename[:-3]
            try:
                file_path = os.path.join(plugins_dir, filename)
                spec = importlib.util.spec_from_file_location(plugin_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "setup"):
                    if asyncio.iscoroutinefunction(module.setup):
                        asyncio.create_task(module.setup(client))
                    else:
                        module.setup(client)
                    logger.info(f"Successfully loaded plugin: {plugin_name}")
                else:
                    logger.warning(f"Plugin {plugin_name} is missing a setup() function.")

            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")


