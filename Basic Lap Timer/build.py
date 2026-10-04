"""Build a self-contained SimHub overlay package. Uses only Python's standard library."""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
NAME = "guysmiley222 - Basic Lap Timer"
SOURCE = ROOT / "dashboard" / NAME
CONNECTED = "[DataCorePlugin.GameRunning] && [DataCorePlugin.CurrentGame] == 'IRacing'"
EMPTY = "--:--.---"


def binding(expression):
    return {"Formula": {"Expression": expression}, "Mode": 2, "TargetPropertyName": "Text"}


def timer(property_name):
    prop = f"[DataCorePlugin.GameData.NewData.{property_name}]"
    # NCalc string literals escape backslashes; .NET TimeSpan formatting escapes punctuation.
    formatted = f"format({prop},'m\\\\:ss\\\\.fff')"
    return (
        f"if({CONNECTED},"
        f"if(isnull({formatted},'') == '','{EMPTY}',"
        f"replace({formatted},'0:00.000','{EMPTY}')),'{EMPTY}')"
    )


def text(name, value, left, top, width, height, size, expression=None, color="#FFFFFFFF"):
    item = {
        "$type": "SimHub.Plugins.OutputPlugins.GraphicalDash.Models.TextItem, SimHub.Plugins",
        "IsTextItem": True, "Name": name, "Text": value,
        "Font": "Consolas", "FontSize": size, "FontWeight": "Normal",
        "TextColor": color, "HorizontalAlignment": 0, "VerticalAlignment": 1,
        "BackgroundColor": "#00FFFFFF", "Left": left, "Top": top,
        "Width": width, "Height": height, "Visible": True, "Opacity": 100,
    }
    if expression:
        item["Bindings"] = {"Text": binding(expression)}
    return item


def build():
    SOURCE.mkdir(parents=True, exist_ok=True)
    items = [{
        "$type": "SimHub.Plugins.OutputPlugins.GraphicalDash.Models.RectangleItem, SimHub.Plugins",
        "IsRectangleItem": True, "Name": "Panel background", "BackgroundColor": "#D910141B",
        "Left": 0, "Top": 0, "Width": 320, "Height": 150, "Visible": True,
        "BorderStyle": {"RadiusTopLeft": 8, "RadiusTopRight": 8,
                        "RadiusBottomLeft": 8, "RadiusBottomRight": 8},
    }]
    items += [
        text("Connection status", "Waiting for iRacing", 14, 8, 292, 20, 13,
             f"if({CONNECTED},'CURRENT LAP','Waiting for iRacing')", "#FFD0D6DE"),
        text("Current lap", EMPTY, 14, 30, 292, 52, 44, timer("CurrentLapTime")),
        text("Last label", "LAST", 14, 94, 140, 18, 12, color="#FFB0BAC8"),
        text("Best label", "SESSION BEST", 166, 94, 140, 18, 12, color="#FFB0BAC8"),
        text("Last lap", EMPTY, 14, 111, 140, 30, 22, timer("LastLapTime")),
        text("Best lap", EMPTY, 166, 111, 140, 30, 22, timer("BestLapTime")),
    ]
    dashboard = {
        "Version": 2, "Id": "fe9e9d8b-98f3-49b8-89e9-935928bd40de",
        "BaseWidth": 320, "BaseHeight": 150, "BackgroundColor": "#00FFFFFF",
        "IsOverlay": True, "EnableClickThroughOverlay": True,
        "Screens": [{"Name": "Lap timer", "ScreenId": "13572486-a604-486c-8300-fd267eb76ed3",
                     "InGameScreen": True, "IdleScreen": True, "PitScreen": True,
                     "BackgroundColor": "#00FFFFFF", "Items": items}],
    }
    metadata = {
        "Title": NAME, "Description": "Current, last, and session-best iRacing lap times.",
        "Author": "guysmiley222", "Width": 320, "Height": 150,
        "ScreenCount": 1, "InGameScreensIndexs": [0], "IdleScreensIndexs": [0],
        "PitScreensIndexs": [0], "MainPreviewIndex": 0, "IsOverlay": True,
        "OverlaySizeWarning": False, "MetadataVersion": 2, "DashboardVersion": "0.1.2",
    }
    for suffix, obj in [(".djson", dashboard), (".djson.metadata", metadata)]:
        (SOURCE / (NAME + suffix)).write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    with ZipFile(SOURCE / (NAME + ".djson.ressources"), "w"):
        pass
    # SimHub's exporter uses CreateFromDirectory(..., includeBaseDirectory=True).
    package = ROOT / (NAME + ".simhubdash")
    with ZipFile(package, "w", ZIP_DEFLATED) as archive:
        for path in sorted(SOURCE.iterdir()):
            archive.write(path, f"{NAME}/{path.name}")
    print(package)


if __name__ == "__main__":
    build()
