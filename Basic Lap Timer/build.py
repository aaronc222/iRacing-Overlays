"""Build a self-contained SimHub overlay package. Uses only Python's standard library."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.overlay import dashboard, panel, text, write_package

ROOT = Path(__file__).resolve().parent
NAME = "guysmiley222 - Basic Lap Timer"
CONNECTED = "[DataCorePlugin.GameRunning] && [DataCorePlugin.CurrentGame] == 'IRacing'"
EMPTY = "--:--.---"


def timer(property_name):
    prop = f"[DataCorePlugin.GameData.NewData.{property_name}]"
    # NCalc string literals escape backslashes; .NET TimeSpan formatting escapes punctuation.
    formatted = f"format({prop},'m\\\\:ss\\\\.fff')"
    return (
        f"if({CONNECTED},"
        f"if(isnull({formatted},'') == '','{EMPTY}',"
        f"replace({formatted},'0:00.000','{EMPTY}')),'{EMPTY}')"
    )


def build():
    items = [panel(320, 150)]
    items += [
        text("Connection status", "Waiting for iRacing", 14, 8, 292, 20, 13,
             f"if({CONNECTED},'CURRENT LAP','Waiting for iRacing')", role="heading"),
        text("Current lap", EMPTY, 14, 30, 292, 52, 44, timer("CurrentLapTime")),
        text("Last label", "LAST", 14, 94, 140, 18, 12, role="muted"),
        text("Best label", "SESSION BEST", 166, 94, 140, 18, 12, role="muted"),
        text("Last lap", EMPTY, 14, 111, 140, 30, 22, timer("LastLapTime")),
        text("Best lap", EMPTY, 166, 111, 140, 30, 22, timer("BestLapTime")),
    ]
    definition = dashboard(items, 320, 150, "fe9e9d8b-98f3-49b8-89e9-935928bd40de",
                           "13572486-a604-486c-8300-fd267eb76ed3", "Lap timer")
    write_package(ROOT, NAME, definition, "Current, last, and session-best iRacing lap times.",
                  "0.2.1", {"Connection status": "CURRENT LAP", "Current lap": "1:18.395",
                            "Last lap": "1:20.123", "Best lap": "1:18.012"})


if __name__ == "__main__":
    build()
