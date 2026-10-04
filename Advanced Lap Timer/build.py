"""Advanced Lap Timer: live splits against SimHub's matching reference laps."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.overlay import dashboard, panel, text, write_package

ROOT = Path(__file__).resolve().parent
NAME = "guysmiley222 - Advanced Lap Timer"
CONNECTED = "[DataCorePlugin.GameRunning] && [DataCorePlugin.CurrentGame] == 'IRacing'"
EMPTY = "--:--.---"
REFERENCES = {
    "session": ("PersistantTrackerPlugin.SessionBest", "PersistantTrackerPlugin.SessionBestLiveDeltaSeconds"),
    "alltime": ("PersistantTrackerPlugin.AllTimeBest", "PersistantTrackerPlugin.AllTimeBestLiveDeltaSeconds"),
}


def formatted_time(property_name):
    return f"format([{property_name}],'m\\\\:ss\\\\.fff')"


def timer(property_name):
    value = formatted_time(property_name)
    return (f"if({CONNECTED},if(isnull({value},'') == '','{EMPTY}',"
            f"replace({value},'0:00.000','{EMPTY}')),'{EMPTY}')")


def split(reference, delta):
    best = formatted_time(reference)
    # Format before comparing null values, avoiding TimeSpan/string comparisons in NCalc.
    missing = f"isnull({best},'') == '' || isnull({best},'') == '0:00.000'"
    seconds = f"format([{delta}],'+0.000;-0.000;+0.000')"
    return (f"if({CONNECTED},if({missing},'--.---',"
            f"if(isnull({seconds},'') == '','--.---',{seconds})),'--.---')")


def build():
    items = [panel(320, 200),
             text("Connection status", "Waiting for iRacing", 14, 8, 292, 20, 13,
                  f"if({CONNECTED},'CURRENT LAP','Waiting for iRacing')", role="heading"),
             text("Current lap", EMPTY, 14, 30, 292, 44, 38,
                  timer("DataCorePlugin.GameData.NewData.CurrentLapTime"))]
    for key, top, title in [("session", 85, "SESSION BEST"), ("alltime", 142, "ALL TIME BEST")]:
        reference, delta = REFERENCES[key]
        items.extend([
            text(f"{key} split label", f"SPLIT VS {title}", 14, top, 176, 16, 10, role="muted"),
            text(f"{key} best label", title, 194, top, 112, 16, 10, role="muted"),
            text(f"{key} split", "--.---", 14, top + 18, 176, 28, 20, split(reference, delta)),
            text(f"{key} best", EMPTY, 194, top + 18, 112, 28, 20, timer(reference)),
        ])
    definition = dashboard(items, 320, 200, "68b8286e-20df-48ea-bb08-3f7cb6ed5488",
                           "ae138595-87b5-4bc0-9e81-643d86172a80", "Advanced lap timer")
    write_package(ROOT, NAME, definition, "Live splits versus session and all-time best lap references.",
                  "0.1.1", {"Connection status": "CURRENT LAP", "Current lap": "1:18.395",
                            "session split": "-0.245", "session best": "1:20.123",
                            "alltime split": "+0.318", "alltime best": "1:18.012"})


if __name__ == "__main__":
    build()
