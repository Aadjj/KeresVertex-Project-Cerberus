import os
import importlib.util
import logging
import asyncio
from typing import Any, Dict

logger = logging.getLogger("Keres.Plugins")


class PluginManager:
    def __init__(self, operator_instance):
        self.operator = operator_instance
        self.plugins_dir = os.path.join(os.path.dirname(__file__), "..", "plugins")
        self.loaded_plugins = []

    async def load_all(self):
        if not os.path.exists(self.plugins_dir):
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return

        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                await self._load_plugin(filename)

    async def _load_plugin(self, filename: str):
        plugin_name = filename[:-3]
        file_path = os.path.join(self.plugins_dir, filename)

        try:
            spec = importlib.util.spec_from_file_location(plugin_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "setup"):
                if asyncio.iscoroutinefunction(module.setup):
                    await module.setup(self.operator)
                else:
                    module.setup(self.operator)

                self.loaded_plugins.append(plugin_name)
                logger.info(f"Plugin Loaded: {plugin_name}")
            else:
                logger.warning(f"Plugin {plugin_name} missing 'setup(operator)' function.")

        except Exception as e:
            logger.exception(f"Failed to load plugin {plugin_name}: {e}")