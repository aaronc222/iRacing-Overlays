# Shared overlay foundation

`overlay.py` builds themed text, translucent panels, dashboard settings, and standalone SimHub packages. It uses Python's standard library. `themes.json` is the source of truth for all six presets.

## Color roles and defaults

| Role | Intended use |
| --- | --- |
| `panel` | Translucent panel background |
| `primary` | Values and main text |
| `heading` | Titles and status headings |
| `muted` | Supporting labels |
| `accent` | Secondary emphasis |
| `success`, `warning`, `danger` | Semantic status indicators |

The shared defaults are Consolas, 14-pixel padding, 8-pixel corners, and `D9` panel alpha (217/255). All text colors are opaque. Current preserves the original Basic Lap Timer styling exactly. Other themes adapt familiar editor palettes for overlays; see [theme notices](THEME_NOTICES.md).

## Builder interface

- `text(name, value, left, top, width, height, size, expression=None, role='primary')`: a themed text component with an optional NCalc value binding.
- `panel(width, height)`: a rounded, themed background.
- `dashboard(items, width, height, dashboard_id, screen_id, screen_name='Overlay')`: a one-screen overlay with a theme dropdown.
- `write_package(root, name, definition, description, version, samples=None)`: writes editable source, metadata, embedded theme definitions, preview samples, notices, and the importable package. Run again after preview generation to include fresh thumbnails.

Each dashboard has a native SettingsBuilder dropdown named **Theme**, read through `Settings.Theme.Key`. Color expressions are generated directly into the dashboard, so an imported overlay needs no Python, repository checkout, internet access, shared SimHub plugin, or JavaScript extension. Settings are managed by SimHub per dashboard. Unknown, empty, and missing theme keys fall back to Current.

The builder includes SettingsBuilder in both the dashboard and its metadata. SimHub uses the metadata to expose the settings UI; defining settings in the dashboard alone does not make the dropdown appear. Verification loads both models and checks that their dropdown identities and options match.

Keep dashboard and settings identities stable for upgrades. Give every new overlay distinct dashboard and screen UUIDs; the theme setting ID is derived from its dashboard UUID. Builds never package a saved user selection.

## Verification

After rebuilding all dashboards and their previews, run from the repository root:

```powershell
python .\shared\verify.py
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File .\shared\verify-themes.ps1
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File '.\Basic Lap Timer\verify.ps1'
```

The Python check validates package completeness and independence, previews, and default-style compatibility. The PowerShell theme check loads the installed SimHub models and evaluates 234 color bindings across all presets plus null/unknown/empty selections. It uses the installed NCalc engine and a .NET equivalent for SimHub's `isnull` handler.

`preview.ps1` renders the generated color expressions in WPF on light and dark backdrops. These are static sample previews, not captures of a running SimHub dashboard. The exact Current preview matches the prior Basic Lap Timer PNG byte for byte.

Native SimHub UI automation is unavailable in this environment. Theme selection, live color refresh, and selection persistence after restarting the overlay remain manual acceptance checks. The underlying settings and generated bindings pass model and expression checks; those checks do not establish runtime UI behavior.
