"""Check complete standalone packages and default-style compatibility without dependencies."""
import json
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shared.overlay import CATALOG, validate_catalog


def verify():
    validate_catalog()
    for folder, name in [("Basic Lap Timer", "guysmiley222 - Basic Lap Timer"),
                         ("Overlay Template", "guysmiley222 - Overlay Template"),
                         ("Advanced Lap Timer", "guysmiley222 - Advanced Lap Timer")]:
        source = ROOT / folder / "dashboard" / name
        definition = json.loads((source / (name + ".djson")).read_text(encoding="utf-8"))
        metadata = json.loads((source / (name + ".djson.metadata")).read_text(encoding="utf-8"))
        assert metadata["Title"] == name and metadata["IsOverlay"] is True
        assert definition["SettingsBuilder"]["Settings"][0]["DefaultValue"] == "current"
        assert len(definition["SettingsBuilder"]["Settings"][0]["Options"]) == 6
        assert metadata["SettingsBuilder"] == definition["SettingsBuilder"], "Settings must be exposed in dashboard metadata"
        required = {name + suffix for suffix in (".djson", ".djson.metadata", ".djson.png",
                                                ".djson.00.png", ".djson.ressources")}
        required |= {"themes.json", "preview-samples.json", "THEME_NOTICES.md"}
        with ZipFile(ROOT / folder / (name + ".simhubdash")) as package:
            assert set(package.namelist()) == {f"{name}/{file}" for file in required}
            assert package.testzip() is None
            for filename in required:
                assert package.read(f"{name}/{filename}") == (source / filename).read_bytes(), filename
            assert json.loads(package.read(f"{name}/themes.json")) == CATALOG
        for key in [theme["key"] for theme in CATALOG["themes"]]:
            assert (ROOT / folder / "previews" / (key + ".png")).is_file()
        print(f"PASS: standalone package, catalog, notices, and six previews: {name}")
        if folder == "Basic Lap Timer":
            assert definition["Id"] == "fe9e9d8b-98f3-49b8-89e9-935928bd40de"
            assert (definition["BaseWidth"], definition["BaseHeight"]) == (320, 150)
            items = definition["Screens"][0]["Items"]
            assert items[0]["BackgroundColor"] == "#D910141B"
            for item in items[1:]:
                assert item["Font"] == "Consolas"
                expected = ("#FFD0D6DE" if item["Name"] == "Connection status" else
                            "#FFB0BAC8" if item["Name"] in ("Last label", "Best label") else "#FFFFFFFF")
                assert item["TextColor"] == expected
            print("PASS: original Basic Lap Timer identity, dimensions, font, and static colors preserved")


if __name__ == "__main__":
    verify()
