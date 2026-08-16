"""Export a current SulcusOS dashboard frame after the bundled research demo runs."""

from __future__ import annotations

import asyncio
import contextlib
import io
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_PACKAGES = ROOT / ".venv" / "Lib" / "site-packages"
if SITE_PACKAGES.exists():
    sys.path.insert(0, str(SITE_PACKAGES))
sys.path.insert(0, str(ROOT))

from examples.research_team.research_team import run_demo  # noqa: E402
from kernel.dashboard import AgentOSDashboard  # noqa: E402


class EmptyTelemetry:
    """Dashboard dependency with intentionally empty telemetry."""


async def capture() -> Path:
    with contextlib.redirect_stdout(io.StringIO()):
        state = await run_demo()

    dashboard = AgentOSDashboard(
        kernel=EmptyTelemetry(),
        bus=EmptyTelemetry(),
        memory=EmptyTelemetry(),
        sandbox=EmptyTelemetry(),
    )
    dashboard.load_research_team_snapshot(state)

    output_dir = ROOT / "showcase" / "assets"
    output_dir.mkdir(parents=True, exist_ok=True)
    async with dashboard.run_test(size=(190, 54)) as pilot:
        await pilot.pause()
        dashboard.refresh_metrics()
        await pilot.pause()
        saved = dashboard.save_screenshot(
            filename="sulcus_dashboard_current.svg",
            path=str(output_dir),
        )
    return Path(saved)


if __name__ == "__main__":
    print(asyncio.run(capture()))

