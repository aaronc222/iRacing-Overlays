"""Build a self-contained SimHub shift-light overlay package. Uses only Python's standard library."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.overlay import DEFAULTS, binding, dashboard, panel, text, themed, write_package

ROOT = Path(__file__).resolve().parent
NAME = "guysmiley222 - Shift Lights"
DASHBOARD_ID = "57e34a5b-eb36-4c95-a1b6-cb18b129b370"
SCREEN_ID = "5cedf18f-8192-4fc5-897c-68094d8de176"
CONNECTED = "[DataCorePlugin.GameRunning] && [DataCorePlugin.CurrentGame] == 'IRacing'"
DATA = "DataCorePlugin.GameData.NewData."
RPM = f"isnull([{DATA}Rpms],0)"
# Prefer SimHub's per-gear redline; fall back to the car redline. Zero means unknown.
REDLINE = (f"if(isnull([{DATA}CarSettings_CurrentGearRedLineRPM],0) > 0,"
           f"[{DATA}CarSettings_CurrentGearRedLineRPM],isnull([{DATA}CarSettings_RedLineRPM],0))")
# Ten LEDs span 70-97% of redline; reaching redline flashes the whole row.
LEDS = [(0.70 + 0.03 * index, role) for index, role in
        enumerate(["success"] * 4 + ["warning"] * 3 + ["danger"] * 3)]
LIT, UNLIT = 100, 15
AT_LIMIT = f"({CONNECTED}) && ({REDLINE}) > 0 && {RPM} >= ({REDLINE})"
SAMPLE_RPM, SAMPLE_REDLINE = 7420, 7900


def number(prop, digits, valid=None):
    value = f"isnull([{DATA}{prop}],-1)"
    check = valid or f"{value} >= 0"
    return f"if({CONNECTED},if({check},format({value},'{'0' * digits}'),'{'-' * digits}'),'{'-' * digits}')"


def led(index, threshold, role, left, top=12, width=26, height=18, radius=4, unlit=UNLIT):
    item = panel(width, height)
    item.update(Name=f"LED {index + 1}", Left=left, Top=top)
    item["BorderStyle"] = {key: radius for key in item["BorderStyle"]}
    themed(item, "BackgroundColor", role)
    lit = f"({CONNECTED}) && ({REDLINE}) > 0 && {RPM} >= ({REDLINE}) * {threshold:.2f}"
    item["Bindings"]["Opacity"] = binding(
        f"if({AT_LIMIT},if(blink('shiftlights',100,true),{LIT},{unlit}),if({lit},{LIT},{unlit}))", "Opacity")
    item["Opacity"] = LIT if SAMPLE_RPM >= SAMPLE_REDLINE * threshold else unlit
    return item


def build():
    padding = DEFAULTS["padding"]
    items = [panel(320, 150)]
    items += [led(index, threshold, role, 16 + index * 29) for index, (threshold, role) in enumerate(LEDS)]
    redline_text = f"if({CONNECTED},if(({REDLINE}) > 0,format({REDLINE},'00000'),'-----'),'-----')"
    items += [
        text("Gear", "-", padding, 38, 92, 84, 76,
             f"if({CONNECTED},isnull([{DATA}Gear],'-'),'-')"),
        text("Gear label", "GEAR", padding, 122, 92, 16, 11, role="muted"),
        text("Connection status", "Waiting for iRacing", 120, 40, 186, 18, 12,
             f"if({CONNECTED},'RPM','Waiting for iRacing')", role="heading"),
        text("RPM", "-----", 120, 56, 186, 40, 34, number("Rpms", 5, f"isnull([{DATA}Rpms],-1) >= 0 && [{DATA}Rpms] <= 99999")),
        text("Throttle label", "THROTTLE %", 120, 102, 90, 16, 11, role="muted"),
        text("Throttle", "---", 120, 116, 90, 24, 20,
             number("Throttle", 3, f"isnull([{DATA}Throttle],-1) >= 0 && [{DATA}Throttle] <= 100")),
        text("Redline label", "REDLINE", 214, 102, 92, 16, 11, role="muted"),
        text("Redline", "-----", 214, 116, 92, 24, 20, redline_text),
    ]
    definition = dashboard(items, 320, 150, DASHBOARD_ID, SCREEN_ID, "Shift lights")
    write_package(ROOT, NAME, definition,
                  "Ten-LED iRacing shift lights that flash at redline, with gear, RPM, throttle, and redline readouts.",
                  "0.1.0", {"Gear": "4", "Connection status": "RPM", "RPM": f"{SAMPLE_RPM:05d}",
                            "Throttle": "058", "Redline": f"{SAMPLE_REDLINE:05d}"})


if __name__ == "__main__":
    build()
