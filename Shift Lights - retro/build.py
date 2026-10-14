"""Shift Lights - retro: the standard shift-light logic drawn as an LCD instrument."""
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.overlay import binding, dashboard, panel, text, write_package
import shared.overlay as style

ROOT = Path(__file__).resolve().parent
NAME = "guysmiley222 - Shift Lights - retro"
DASHBOARD_ID = "5137047f-e168-4073-ac6e-6be08e4c82f1"
SCREEN_ID = "c6f1d631-3c41-4de5-8f5f-da0fd4058c73"

# Reuse the standard overlay's LED thresholds and readout formulas so both variants behave identically.
_spec = importlib.util.spec_from_file_location("shift_lights", ROOT.parent / "Shift Lights" / "build.py")
standard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(standard)
CONNECTED, DATA, REDLINE = standard.CONNECTED, standard.DATA, standard.REDLINE

# Local retro palettes: shared defaults and other overlays remain untouched.
style.DEFAULTS["panelAlpha"] = "FF"
style.DEFAULTS["cornerRadius"] = 0
monokai = next(theme for theme in style.THEMES if theme["key"] == "monokai")
monokai["colors"]["muted"] = monokai["colors"]["heading"]
monokai["colors"]["primary"] = "#C8E69A"

UNLIT = 10
DIGITS = {'0': 'abcdef', '1': 'bc', '2': 'abdeg', '3': 'abcdg', '4': 'bcfg',
          '5': 'acdfg', '6': 'acdefg', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg', '-': 'g'}
# Gear displays use the conventional lowercase seven-segment n and r.
GEARS = {**{d: DIGITS[d] for d in '123456789'}, 'N': 'ceg', 'R': 'eg'}


def rect(name, left, top, width, height, role="panel"):
    item = panel(width, height)
    item.update(Name=name, Left=left, Top=top)
    if role != "panel":
        style.themed(item, "BackgroundColor", role)
    return item


def seven(name, expression, places, number, sample, left, top, height):
    """Seven-segment digits for the hidden text item `name`; number=None renders the gear string."""
    width = round(height * .58, 2)
    advance = round(width * 1.3, 2)
    thick = round(max(2, height * .09), 2)
    middle = round((height - thick) / 2, 2)
    lower = height - middle - 2 * thick - 1
    geometry = {'a': (thick, 0, width - 2 * thick, thick), 'g': (thick, middle, width - 2 * thick, thick),
                'd': (thick, height - thick, width - 2 * thick, thick),
                'f': (0, thick, thick, middle - thick - 1), 'b': (width - thick, thick, thick, middle - thick - 1),
                'e': (0, middle + thick + 1, thick, lower), 'c': (width - thick, middle + thick + 1, thick, lower)}
    missing = f"({expression}) == '{'-' * places}'"
    items = []
    for position in range(places):
        x = left + position * advance
        cell = rect(f"{name} digit {position} cell", x - 1, top - 2, width + 2, height + 4)
        cell.pop("Bindings", None)
        cell["BackgroundColor"] = "#28000000"
        items.append(cell)
        for segment, (dx, dy, w, h) in geometry.items():
            if number is None:
                matches = ' || '.join(f"({expression}) == '{gear}'" for gear, lit in GEARS.items() if segment in lit)
            else:
                value = f"Floor(({number}) / {10 ** (places - 1 - position)}) % 10"
                matches = ' || '.join(f"({value}) == {d}" for d in '0123456789' if segment in DIGITS[d])
            active = f"if({missing},{'true' if segment == 'g' else 'false'},({matches}))"
            item = rect(f"{name} digit {position} {segment}", round(x + dx, 2), round(top + dy, 2),
                        round(w, 2), round(h, 2), "primary")
            item["Bindings"]["Opacity"] = binding(f"if({active},100,{UNLIT})", "Opacity")
            item["Opacity"] = 100 if segment in GEARS.get(sample[position], DIGITS.get(sample[position], '')) else UNLIT
            items.append(item)
    return items


def build():
    items = [rect("Bezel", 0, 0, 320, 150), rect("LCD face", 7, 7, 306, 136)]
    items[0]["BackgroundColor"] = "#FF242725"
    items[0].pop("Bindings", None)
    items += [standard.led(index, threshold, role, 16 + index * 29, top=14, height=12, radius=0, unlit=UNLIT)
              for index, (threshold, role) in enumerate(standard.LEDS)]
    items += [rect("LED rule", 14, 33, 292, 1, "muted"), rect("Column rule", 104, 40, 1, 96, "muted"),
              rect("Readout rule", 114, 100, 192, 1, "muted")]
    # Hidden text items keep the standard formulas; segments mirror them for verification.
    readouts = [
        ("Gear", "-", f"if({CONNECTED},isnull([{DATA}Gear],'-'),'-')", 1, None, "4", 40, 60, 66),
        ("RPM", "-----", standard.number("Rpms", 5, f"isnull([{DATA}Rpms],-1) >= 0 && [{DATA}Rpms] <= 99999"),
         5, f"Floor(isnull([{DATA}Rpms],0) + 0.5)", f"{standard.SAMPLE_RPM:05d}", 116, 60, 32),
        ("Throttle", "---", standard.number("Throttle", 3, f"isnull([{DATA}Throttle],-1) >= 0 && [{DATA}Throttle] <= 100"),
         3, f"Floor(isnull([{DATA}Throttle],0) + 0.5)", "058", 116, 120, 18),
        ("Redline", "-----", f"if({CONNECTED},if(({REDLINE}) > 0,format({REDLINE},'00000'),'-----'),'-----')",
         5, f"Floor(({REDLINE}) + 0.5)", f"{standard.SAMPLE_REDLINE:05d}", 216, 120, 18),
    ]
    for name, empty, expression, places, number, sample, left, top, height in readouts:
        hidden = text(name, empty, left, top, 60, height, 12, expression)
        hidden["Visible"] = False
        items.append(hidden)
        items += seven(name, expression, places, number, sample, left, top, height)
    items += [
        text("Gear label", "GEAR", 14, 38, 86, 16, 10, role="muted"),
        text("Connection status", "Waiting for iRacing", 114, 38, 192, 18, 12,
             f"if({CONNECTED},'RPM','Waiting for iRacing')", role="heading"),
        text("Throttle label", "THROTTLE %", 114, 103, 96, 16, 10, role="muted"),
        text("Redline label", "REDLINE", 214, 103, 92, 16, 10, role="muted"),
    ]
    definition = dashboard(items, 320, 150, DASHBOARD_ID, SCREEN_ID, "Retro shift lights")
    write_package(ROOT, NAME, definition,
                  "Retro LCD shift lights that flash at redline, with seven-segment gear, RPM, throttle, and redline.",
                  "0.1.0", {"Connection status": "RPM"})


if __name__ == "__main__":
    build()
