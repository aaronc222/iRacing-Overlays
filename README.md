# iRacing Overlays

A growing collection of SimHub overlays for iRacing by **guysmiley222**. Each overlay has its own folder with an importable dashboard, editable source, and setup instructions.

| Overlay | Description | Download and setup |
| --- | --- | --- |
| Basic Lap Timer | Current, last, and session-best lap times in a compact translucent panel | [Basic Lap Timer](Basic%20Lap%20Timer/) |
| Advanced Lap Timer | Current lap plus live splits and matching session/all-time best references | [Advanced Lap Timer](Advanced%20Lap%20Timer/) |
| Advanced Lap Timer - retro | Native seven-segment LCD styling with matching lap references | [Retro lap timer](Advanced%20Lap%20Timer%20-%20retro/) |
| Tire Temp and Pressure | Four-corner average temperature (�C) and cold pressure (PSI) | [Standard](Tire%20Temp%20and%20Pressure/) |
| Tire Temp and Pressure - retro | The same readings with LCD seven-segment instruments | [Retro](Tire%20Temp%20and%20Pressure%20-%20retro/) |

## Getting started

Install [SimHub](https://www.simhubdash.com/), select iRacing, and import the `.simhubdash` file from the overlay's folder. Run it through **Dash Studio → Overlays** while iRacing is in windowed or borderless mode.

See each overlay's README for details, a preview, and rebuilding instructions.

## Themes and new overlays

Every build generates six fixed-color `.simhubdash` packages in each overlay's `themed/` folder: **Current**, **VS Code Dark+**, **Dracula**, **Nord**, **Monokai**, and **Solarized Dark**. The theme appears in the filename and SimHub display name. Import the version you want; no settings dropdown is needed. Each theme has a stable, distinct dashboard identity, so variants can coexist.

Start new overlays from [Overlay Template](Overlay%20Template/). The [shared foundation](shared/) provides reusable components, palettes, packaging, and verification. Imported packages include their color bindings and require no additional plugin or repository checkout.
