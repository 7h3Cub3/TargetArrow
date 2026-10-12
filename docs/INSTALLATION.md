# Installation

TargetArrow is built and tested for **HorizonXI with Ashita 4**. It requires HideParty to be enabled and actively hiding the native party and target frames.

1. Download the installable `TargetArrow-vX.Y.Z.zip` from [GitHub Releases](https://github.com/7h3Cub3/TargetArrow/releases).
2. Extract it into `HorizonXI\Game\addons\` so that `HorizonXI\Game\addons\targetarrow\targetarrow.lua` and the PNG files are present.
3. Enable HideParty in the HorizonXI launcher addon options, if listed, and configure it to hide the native party and target UI.
4. To start TargetArrow automatically, open `HorizonXI\Game\scripts\default.txt` and add `/addon load targetarrow` to the user-editable area under **Custom user plugins and addons**.
5. Save the startup configuration and launch the game.

Custom addons may not appear in the launcher addon list. The startup script is the standard way to load them automatically.

## Updating

Extract the latest addon ZIP over the existing `targetarrow` directory and restart the game. The local `settings.lua` file is excluded from release ZIPs, preserving your preferences.

## Removing

Remove the `targetarrow` folder and its entry from the startup script. HideParty is managed separately.
