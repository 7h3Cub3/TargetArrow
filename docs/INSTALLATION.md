# Installation

TargetArrow was built and tested for **HorizonXI with Ashita 4**. It requires **HideParty**, configured to hide the native party and target frames.

1. Download **TargetArrow-1.0.zip** from [GitHub Releases](https://github.com/7h3Cub3/TargetArrow/releases).
2. Extract the ZIP into `HorizonXI\Game\addons\`, resulting in `HorizonXI\Game\addons\targetarrow\targetarrow.lua` and the accompanying PNG cursor files.
3. Open the **HorizonXI launcher** and enable **HideParty** in the Addons section. Configure HideParty to hide the native party and target interface.
4. Enable TargetArrow using **one** of these methods:

   **Method A — HorizonXI launcher (recommended):** Open the **Addons** section and enable **TargetArrow**. Start the game normally; the launcher loads the addon.

   **Method B — Ashita startup script:** If TargetArrow is not listed in the launcher, open `HorizonXI\Game\scripts\default.txt` and add `/addon load targetarrow` under **Custom user plugins and addons** in the user-editable section.

5. Save your configuration and launch HorizonXI. The target cursor displays when HideParty is active and hiding the native interface.

Do not configure both activation methods simultaneously. The launcher may not list every manually installed Ashita addon; the startup-script method remains available.

## Updating

Replace the installed files with those from the latest ZIP and restart HorizonXI. Local `settings.lua` is excluded from the release package to preserve your preferences.

## Removing

Disable TargetArrow in the launcher, or remove its entry from `default.txt` if using the startup-script method. Delete the `targetarrow` folder from `HorizonXI\Game\addons\` to remove the addon. HideParty is managed separately.
