# Installation

There is **no installer** and no modification to HideParty or XIUI.

1. Ensure the official Ashita 4 `hideparty` addon is installed and not modified to keep the native target primitive visible.
2. Extract `TargetArrow-v1.0.0.zip` into the game's `Game/addons/` folder. The archive includes `targetarrow/targetarrow.lua`, `arrow.png`, `subarrow.png`, `arrow-neutral.png`, `subarrow-neutral.png` and `LICENSE`.
3. Run `/addon load hideparty`, `/hideparty hide`, `/addon load targetarrow`.
4. Select a visible target and run `/ta status`.

When updating, `/addon unload targetarrow` before replacing its three code/asset files. Leave `settings.lua` untouched to retain options; then `/addon load targetarrow`.

To uninstall, unload TargetArrow and delete `Game/addons/targetarrow`. HideParty is unaffected.
