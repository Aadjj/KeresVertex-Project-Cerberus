import os
import importlib.util
import glob
import logging
from typing import List, Optional, Dict

logger = logging.getLogger("Keres.Beacon.Plugins")


class BeaconPlugin:
    def __init__(self):
        self.name = self.__class__.__name__

    async def run(self, args: list) -> str:
        raise NotImplementedError("Plugins must implement the run() method.")


def load_beacon_plugins(plugin_dir: str) -> Dict[str, BeaconPlugin]:
    loaded_plugins = {}

    if not os.path.exists(plugin_dir):
        os.makedirs(plugin_dir)
        return loaded_plugins

    plugin_files = glob.glob(os.path.join(plugin_dir, "*.py"))

    for plugin_path in plugin_files:
        module_name = os.path.basename(plugin_path)[:-3]
        if module_name == "__init__":
            continue

        try:
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "Plugin"):
                instance = module.Plugin()
                if isinstance(instance, BeaconPlugin):
                    loaded_plugins[module_name] = instance
                    logger.info(f"[*] Capability loaded: {module_name}")

        except Exception as e:
            logger.error(f"[-] Failed to load plugin {module_name}: {e}")

    return loaded_plugins