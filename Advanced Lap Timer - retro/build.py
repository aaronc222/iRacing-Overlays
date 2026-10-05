"""Advanced Lap Timer: live splits against SimHub's matching reference laps."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.overlay import dashboard, panel, text, write_package
import shared.overlay as style
from segments import readout

ROOT = Path(__file__).resolve().parent
NAME = "guysmiley222 - Advanced Lap Timer - retro"
CONNECTED = "[DataCorePlugin.GameRunning] && [DataCorePlugin.CurrentGame] == 'IRacing'"
EMPTY = "--:--.---"
REFERENCES = {
    "session": ("PersistantTrackerPlugin.SessionBest", "PersistantTrackerPlugin.SessionBestLiveDeltaSeconds"),
    "alltime": ("PersistantTrackerPlugin.AllTimeBest", "PersistantTrackerPlugin.AllTimeBestLiveDeltaSeconds"),
}


def formatted_time(property_name):
    return f"format([{property_name}],'mm\\\\:ss\\\\.fff')"


def timer(property_name):
    value = formatted_time(property_name)
    return (f"if({CONNECTED},if(isnull({value},'') == '','{EMPTY}',"
            f"replace({value},'00:00.000','{EMPTY}')),'{EMPTY}')")


def split(reference, delta):
    best = formatted_time(reference)
    # Format before comparing null values, avoiding TimeSpan/string comparisons in NCalc.
    missing = f"isnull({best},'') == '' || isnull({best},'') == '00:00.000'"
    seconds = f"format([{delta}],'+000.000;-000.000;+000.000')"
    return (f"if({CONNECTED},if({missing},'---.---',"
            f"if(isnull({seconds},'') == '','---.---',{seconds})),'---.---')")


# Local retro palettes: shared defaults and other overlays remain untouched.
style.DEFAULTS["panelAlpha"] = "FF"
style.DEFAULTS["cornerRadius"] = 0
monokai = next(theme for theme in style.THEMES if theme["key"] == "monokai")
monokai["colors"]["muted"] = monokai["colors"]["heading"]
monokai["colors"]["primary"] = "#C8E69A"
def instrument_rect(name, left, top, width, height, role="panel"):
    item = panel(width, height)
    item.update(Name=name, Left=left, Top=top)
    if role != "panel":
        style.themed(item, "BackgroundColor", role)
    return item

def build():
    items = [instrument_rect("Bezel", 0, 0, 320, 200),
             instrument_rect("LCD face", 7, 7, 306, 186),
             instrument_rect("Main divider", 14, 78, 292, 1, "muted"),
             instrument_rect("Reference divider", 14, 136, 292, 1, "muted"),
             instrument_rect("Column divider", 186, 85, 1, 103, "muted"),
             text("Connection status", "Waiting for iRacing", 14, 8, 292, 20, 13,
                  f"if({CONNECTED},'CURRENT LAP','Waiting for iRacing')", role="heading"),
             text("Current lap", EMPTY, 14, 30, 292, 44, 38,
                  timer("DataCorePlugin.GameData.NewData.CurrentLapTime"))]
    for key, top, title in [("session", 85, "SESSION BEST"), ("alltime", 142, "ALL TIME BEST")]:
        reference, delta = REFERENCES[key]
        items.extend([
            text(f"{key} split label", f"SPLIT VS {title}", 14, top, 176, 16, 10, role="muted"),
            text(f"{key} best label", title, 194, top, 112, 16, 10, role="muted"),
            text(f"{key} split", "---.---", 14, top + 18, 176, 28, 20, split(reference, delta)),
            text(f"{key} best", EMPTY, 194, top + 18, 112, 28, 20, timer(reference)),
        ])
    samples = {"Current lap": "59:59.999", "session split": "-599.999",
               "session best": "59:59.999", "alltime split": "+599.999", "alltime best": "59:59.999"}
    for item in list(items):
        if item["Name"] not in samples:
            continue
        item["Visible"] = False  # Retain the original text formulas for verification.
        name = item["Name"]
        is_split = name.endswith(" split")
        if name == "Current lap":
            prop = "DataCorePlugin.GameData.NewData.CurrentLapTime"
        else:
            prop = REFERENCES[name.split()[0]][1 if is_split else 0]
        value = f"isnull([{prop}],0)" if is_split else f"timespantoseconds(isnull([{prop}],0))"
        number = (f"Round(Abs({value}) * 1000,0)", value) if is_split else f"Floor(Round(({value}) * 1000,4))"
        items.extend(readout(instrument_rect, name, item["Bindings"]["Text"]["Formula"]["Expression"],
                             number, samples[name], item["Left"], item["Top"]+4,
                             240 if name == "Current lap" else (142 if is_split else 109),
                             34 if name == "Current lap" else 18, is_split))
    items[0]["BackgroundColor"] = "#FF242725"
    items[0].pop("Bindings", None)
    definition = dashboard(items, 320, 200, "f37738a9-304c-45ae-b56f-d7e123897a82",
                           "fb9a8278-d6e5-4a8d-a9ac-21d8a3c04055", "Retro LCD lap timer")
    write_package(ROOT, NAME, definition, "Live splits versus session and all-time best lap references.",
                  "0.2.2", {"Connection status": "CURRENT LAP", "Current lap": "59:59.999",
                            "session split": "-599.999", "session best": "59:59.999",
                            "alltime split": "+599.999", "alltime best": "59:59.999"})


if __name__ == "__main__":
    build()
