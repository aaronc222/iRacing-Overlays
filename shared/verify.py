"""Check complete standalone packages and default-style compatibility without dependencies."""
import json
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shared.overlay import CATALOG, validate_catalog, color, theme_expression, ROLES


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
        ids = set()
        for theme in CATALOG['themes']:
            title = f"{name} [{theme['label']}]"
            with ZipFile(ROOT / folder / 'themed' / (title + '.simhubdash')) as package:
                compiled = json.loads(package.read(f'{title}/{title}.djson'))
                info = json.loads(package.read(f'{title}/{title}.djson.metadata'))
                assert 'SettingsBuilder' not in compiled and 'SettingsBuilder' not in info
                assert info['Title'] == title
                assert compiled['Id'] not in ids and compiled['Id'] != definition['Id']
                ids.add(compiled['Id'])
                assert package.testzip() is None
                assert package.read(f'{title}/{title}.djson.png') == (ROOT / folder / 'previews' / (theme['key'] + '.png')).read_bytes()
                for original, item in zip(definition['Screens'][0]['Items'], compiled['Screens'][0]['Items']):
                    for target in ('TextColor', 'BackgroundColor'):
                        if target in original.get('Bindings', {}):
                            expression = original['Bindings'][target]['Formula']['Expression']
                            role = next(role for role in ROLES if theme_expression(role) == expression)
                            assert item[target] == color(role, theme['key'])
                            assert target not in item.get('Bindings', {})
                    assert item.get('Bindings', {}).get('Text') == original.get('Bindings', {}).get('Text')
        print(f'PASS: six fixed-color themed packages with unique identities, matching thumbnails, and unchanged timing: {name}')
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
