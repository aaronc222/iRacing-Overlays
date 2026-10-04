"""Copy this folder, give the dashboard new persistent IDs, then replace the sample content."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.overlay import DEFAULTS, dashboard, panel, text, write_package

ROOT = Path(__file__).resolve().parent
NAME = "guysmiley222 - Overlay Template"
# Generate new UUIDs once for each new overlay; retain them across future rebuilds.
DASHBOARD_ID = "f2e683a6-ec2d-4621-990f-cecf2e86b17c"
SCREEN_ID = "ce8c6db1-5e97-48f5-84d9-f08e27c3d1a0"


def build():
    padding = DEFAULTS["padding"]
    items = [panel(320, 150),
             text("Title", "OVERLAY TEMPLATE", padding, 8, 292, 22, 15, role="heading"),
             text("Value", "1:18.395", padding, 32, 292, 48, 40),
             text("Label", "Shared theme components", padding, 82, 292, 20, 13, role="muted")]
    for index, role in enumerate(("accent", "success", "warning", "danger")):
        items.append(text(role.title(), role.upper(), padding + index * 75, 115, 73, 22, 11, role=role))
    write_package(ROOT, NAME, dashboard(items, 320, 150, DASHBOARD_ID, SCREEN_ID),
                  "Reusable themed SimHub overlay starter.", "0.1.0")


if __name__ == "__main__":
    build()
