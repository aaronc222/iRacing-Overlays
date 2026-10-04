"""Standard-library-only SimHub components, theme settings, and packaging."""
import json
import re
from copy import deepcopy
from pathlib import Path
from uuid import UUID, uuid5
from zipfile import ZipFile, ZIP_DEFLATED

SHARED = Path(__file__).resolve().parent
ROLES = {"panel", "primary", "heading", "muted", "accent", "success", "warning", "danger"}
CATALOG = json.loads((SHARED / "themes.json").read_text(encoding="utf-8"))
DEFAULTS = CATALOG["defaults"]
THEMES = CATALOG["themes"]
DEFAULT_THEME = CATALOG["defaultTheme"]


def validate_catalog():
    keys = [theme["key"] for theme in THEMES]
    if len(keys) != len(set(keys)) or DEFAULT_THEME not in keys:
        raise ValueError("Theme keys must be unique and include the default")
    for theme in THEMES:
        if set(theme["colors"]) != ROLES:
            raise ValueError(f"Incomplete palette: {theme['key']}")
        if not all(re.fullmatch(r"#[0-9A-F]{6}", value) for value in theme["colors"].values()):
            raise ValueError(f"Invalid RGB color: {theme['key']}")


validate_catalog()


def color(role, theme_key=DEFAULT_THEME):
    theme = next((theme for theme in THEMES if theme["key"] == theme_key),
                 next(theme for theme in THEMES if theme["key"] == DEFAULT_THEME))
    return "#" + (DEFAULTS["panelAlpha"] if role == "panel" else "FF") + theme["colors"][role][1:]


def binding(expression, target="Text"):
    return {"Formula": {"Expression": expression}, "Mode": 2, "TargetPropertyName": target}


def theme_expression(role):
    # SettingsBuilder ComboboxEntry exposes its selected option as Settings.Theme.Key.
    result = f"'{color(role)}'"
    for theme in reversed(THEMES):
        if theme["key"] != DEFAULT_THEME:
            result = (f"if(isnull([Settings.Theme.Key],'current') == '{theme['key']}',"
                      f"'{color(role, theme['key'])}',{result})")
    return result


def themed(item, target, role):
    item[target] = color(role)
    item.setdefault("Bindings", {})[target] = binding(theme_expression(role), target)
    return item


def panel(width, height):
    radius = DEFAULTS["cornerRadius"]
    return themed({
        "$type": "SimHub.Plugins.OutputPlugins.GraphicalDash.Models.RectangleItem, SimHub.Plugins",
        "IsRectangleItem": True, "Name": "Panel background", "Left": 0, "Top": 0,
        "Width": width, "Height": height, "Visible": True,
        "BorderStyle": {key: radius for key in
                        ("RadiusTopLeft", "RadiusTopRight", "RadiusBottomLeft", "RadiusBottomRight")},
    }, "BackgroundColor", "panel")


def text(name, value, left, top, width, height, size, expression=None, role="primary"):
    item = {
        "$type": "SimHub.Plugins.OutputPlugins.GraphicalDash.Models.TextItem, SimHub.Plugins",
        "IsTextItem": True, "Name": name, "Text": value,
        "Font": DEFAULTS["font"], "FontSize": size, "FontWeight": "Normal",
        "HorizontalAlignment": 0, "VerticalAlignment": 1,
        "BackgroundColor": "#00FFFFFF", "Left": left, "Top": top,
        "Width": width, "Height": height, "Visible": True, "Opacity": 100,
    }
    if expression:
        item["Bindings"] = {"Text": binding(expression)}
    return themed(item, "TextColor", role)


def dashboard(items, width, height, dashboard_id, screen_id, screen_name="Overlay"):
    return {
        "Version": 2, "Id": dashboard_id, "BaseWidth": width, "BaseHeight": height,
        "BackgroundColor": "#00FFFFFF", "IsOverlay": True, "EnableClickThroughOverlay": True,
        "SettingsBuilder": {"Settings": [{
            "$type": "SimHub.Plugins.SettingsBuilderModule.ComboboxEntry, SimHub.Plugins",
            "Options": [{"Key": theme["key"], "Label": theme["label"]} for theme in THEMES],
            "PropertyName": "Theme", "DefaultValue": DEFAULT_THEME,
            "TypeName": "ComboboxEntry", "Label": "Theme",
            "Id": str(uuid5(UUID(dashboard_id), "Theme")),
        }]},
        "Screens": [{"Name": screen_name, "ScreenId": screen_id, "InGameScreen": True,
                     "IdleScreen": True, "PitScreen": True, "BackgroundColor": "#00FFFFFF",
                     "Items": items}],
    }


def write_package(root, name, definition, description, version, samples=None):
    root = Path(root)
    source = root / "dashboard" / name
    source.mkdir(parents=True, exist_ok=True)
    metadata = {
        "SettingsBuilder": definition["SettingsBuilder"],
        "Title": name, "Description": description, "Author": "guysmiley222",
        "Width": definition["BaseWidth"], "Height": definition["BaseHeight"],
        "ScreenCount": 1, "InGameScreensIndexs": [0], "IdleScreensIndexs": [0],
        "PitScreensIndexs": [0], "MainPreviewIndex": 0, "IsOverlay": True,
        "OverlaySizeWarning": False, "MetadataVersion": 2, "DashboardVersion": version,
    }
    for filename, value in [(name + ".djson", definition), (name + ".djson.metadata", metadata),
                            ("themes.json", CATALOG), ("preview-samples.json", samples or {})]:
        (source / filename).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    (source / "THEME_NOTICES.md").write_text((SHARED / "THEME_NOTICES.md").read_text(encoding="utf-8"), encoding="utf-8")
    with ZipFile(source / (name + ".djson.ressources"), "w"):
        pass
    package = root / (name + ".simhubdash")
    # Package only the dashboard's files, not settings persisted by a running SimHub install.
    names = [name + suffix for suffix in (".djson", ".djson.metadata", ".djson.ressources",
                                         ".djson.png", ".djson.00.png")]
    names += ["themes.json", "preview-samples.json", "THEME_NOTICES.md"]
    with ZipFile(package, "w", ZIP_DEFLATED) as archive:
        for filename in names:
            path = source / filename
            if path.exists():
                archive.write(path, f"{name}/{filename}")
    print(package)
    write_themed_packages(root, name, definition, metadata)
    return package


def write_themed_packages(root, name, definition, metadata):
    """Compile every palette to literal colors with separate, stable import identities."""
    output = root / "themed"
    output.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        title = f"{name} [{theme['label']}]"
        compiled = deepcopy(definition)
        compiled.pop("SettingsBuilder", None)
        compiled["Id"] = str(uuid5(UUID(definition["Id"]), "compiled-theme:" + theme["key"]))
        for screen in compiled["Screens"]:
            screen["ScreenId"] = str(uuid5(UUID(screen["ScreenId"]), theme["key"]))
            for item in screen["Items"]:
                bindings = item.get("Bindings", {})
                for target in ("TextColor", "BackgroundColor"):
                    if target in bindings:
                        expression = bindings[target]["Formula"]["Expression"]
                        role = next(role for role in ROLES if theme_expression(role) == expression)
                        item[target] = color(role, theme["key"])
                        del bindings[target]
                if not bindings:
                    item.pop("Bindings", None)
        info = deepcopy(metadata)
        info.pop("SettingsBuilder", None)
        info["Title"] = title
        info["Description"] += " Theme: " + theme["label"] + "."
        package = output / (title + ".simhubdash")
        with ZipFile(package, "w", ZIP_DEFLATED) as archive:
            for suffix, value in ((".djson", compiled), (".djson.metadata", info)):
                archive.writestr(f"{title}/{title}{suffix}", json.dumps(value, indent=2) + "\n")
            archive.writestr(f"{title}/{title}.djson.ressources", (root / "dashboard" / name / (name + ".djson.ressources")).read_bytes())
            archive.writestr(f"{title}/THEME_NOTICES.md", (SHARED / "THEME_NOTICES.md").read_bytes())
            preview = root / "previews" / (theme["key"] + ".png")
            if preview.exists():
                for suffix in (".djson.png", ".djson.00.png"):
                    archive.write(preview, f"{title}/{title}{suffix}")
        print(package)
