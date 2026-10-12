# Configuration

Open the in-game configuration with **`/ta config`**. The ImGui window does not open automatically, and can be closed with the X or Close button.

The menu also includes **Restore Defaults**. Pressing it immediately restores every shipped default (including scale `1.0`, vertical offset `4`, fallback model height `1.9`, classic gold/green cursor colors and custom color values). Bobbing and flashing are switched **off**, and the addon is re-enabled for the current session. Your local `settings.lua` is updated immediately, so these defaults remain after a reload. The window stays open. The HideParty safety checks cannot be disabled by resetting settings.

The menu provides the original **Scale**, **Vertical offset**, and **Fallback model height** settings alongside separate **Target arrow** and **Subtarget arrow** color dropdowns, animation checkboxes, and editable animation parameters.

## Colors

Color modes: `Original`, `Red`, `Blue`, `Green`, `Gold`, `Purple`, `Cyan`, `White`, or `Custom` RGB. `Original` displays the two unchanged historical cursor PNGs (gold for a target, green for a subtarget). Every other mode uses a grayscale-tintable copy of that exact silhouette; it does not change its shape or anchoring.

Commands: `/ta color red` and `/ta subcolor blue`. Use `original` to restore the classic colors. Choose Custom in the menu to get a full RGB color editor. Target and subtarget choices are stored independently.

## Optional animation

**Off by default** on new installations:

- **Bobbing** (`/ta bob on|off`): rises and falls sinusoidally around the same skeleton anchor; adjustable rate (0.1–5 cycles/s) and distance (0–30 pixels).
- **Flashing** (`/ta flash on|off`): opacity cycles from full brightness to a configurable lower opacity; adjustable rate (0.1–5 cycles/s) and strength (0–0.85).

Both effects can be used independently or together, and neither changes HideParty detection or target acquisition.

## Existing commands

`/ta status`, `/ta on`, `/ta off`, `/ta toggle`, `/ta scale 1.0`, `/ta offset 4`, and `/ta height 1.9` continue to work. `/targetarrow` remains the full alias.

All numeric and color/animation settings are stored in `settings.lua` in the addon directory, which is neither included in source control nor in the release ZIP. Loading the addon never executes this file as Lua code. The session-only `/ta on/off` setting resets to enabled on addon reload. Settings are automatically saved as you change them in the UI.
