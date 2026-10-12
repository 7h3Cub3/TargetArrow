# TargetArrow

[![Checks](https://github.com/7h3Cub3/TargetArrow/actions/workflows/check.yml/badge.svg)](https://github.com/7h3Cub3/TargetArrow/actions/workflows/check.yml)
[![Build ZIPs](https://github.com/7h3Cub3/TargetArrow/actions/workflows/release.yml/badge.svg)](https://github.com/7h3Cub3/TargetArrow/actions/workflows/release.yml)

**TargetArrow** is an open-source Ashita 4 addon for Final Fantasy XI / HorizonXI, authored by **7h3Cub3**.

Repository: https://github.com/7h3Cub3/TargetArrow  
License: **GPL-3.0-or-later** (see [LICENSE](LICENSE))  
Version: **1.0.0** — held at 1.0.0 during testing until the initial stable release is confirmed.

## Why TargetArrow exists

The stock [HideParty addon](https://github.com/AshitaXI/Ashita-v4beta/blob/main/addons/hideparty/hideparty.lua) hides FFXI's original party and target frames. Unfortunately, the native on-world arrow marking your target shares a UI primitive with the original target HP frame. Hiding that frame also removes the arrow. A custom UI such as XIUI replaces the target frame but not the on-world pointer.

**TargetArrow restores the world-space target pointer without restoring the native target window.** It is designed to run *alongside the original, unmodified HideParty*; XIUI is optional. It draws a gold arrow above the selected target and a green arrow while selecting a subtarget.

## HideParty is mandatory

TargetArrow uses a read-only, fail-closed guard checked on every frame. The arrow draws only when:

1. Ashita reports `hideparty` is loaded (`AddonManager:IsLoaded('hideparty')`).
2. The game's native party primitive is actually hidden.
3. The game's native target frame/arrow primitive is actually hidden.
4. An eligible selected target can be projected onto the screen.

`/hideparty show`, unloading HideParty, missing HideParty, or an unreadable UI state **automatically suppresses the arrow**. `/ta on` never bypasses the guard. TargetArrow does not modify native UI memory or patch HideParty.

## Installation — no installer required

Download **TargetArrow-v1.0.0.zip** from a GitHub Release (or the Actions build artifacts), then extract directly into your game's `Game\addons` directory. The ZIP contains a `targetarrow` folder:

```text
E:\HorizonXI\Game\addons\targetarrow\targetarrow.lua
E:\HorizonXI\Game\addons\targetarrow\arrow.png
E:\HorizonXI\Game\addons\targetarrow\subarrow.png
E:\HorizonXI\Game\addons\targetarrow\arrow-neutral.png
E:\HorizonXI\Game\addons\targetarrow\subarrow-neutral.png
```

Alternatively, copy the five corresponding addon files from the **repository root** into `Game\addons\targetarrow\`. No PowerShell installer, original HideParty files, or third-party dependencies are bundled.

In FFXI:

```text
/addon load hideparty
/hideparty hide
/addon load targetarrow
/ta status
```

Reload after updating with `/addon reload targetarrow`. The original HideParty must be restored if an earlier patch forced its target primitive to stay visible.

## Screenshots — original vs TargetArrow

The two screenshots below are taken from the actual game. The character name and
its blue icon have been erased for privacy; **the cursor pixels, character and
other gameplay pixels were left unchanged**. The silver cursor on the left is
the game's normal marker; the gold cursor on the right is TargetArrow's restored
original artwork.

| Native FFXI target cursor | TargetArrow cursor |
|:---:|:---:|
| ![Native silver target cursor](screenshots/original-hideparty.png) | ![TargetArrow gold replacement cursor](screenshots/targetarrow.png) |

## Configuration window

Type **`/ta config`** to open or close the Ashita 4 ImGui settings window.
The window does not open automatically. Settings apply immediately and persist
in a local `settings.lua` file, except the session-only enable/disable switch.

The window also has **Restore Defaults**, which reapplies the original gold/green arrows, scale `1.0`, offset `4`, fallback height `1.9`, and default color/animation parameters. It switches both animations off, re-enables TargetArrow for the session, and saves the defaults immediately to local `settings.lua`. It does not change HideParty or override its safety guard.

The window provides:

- Current HideParty validation and rendering state.
- Size, vertical screen offset and fallback height.
- **Independent target and subtarget arrow colors:** Original (the original
  gold/green PNGs, pixel-for-pixel), Red, Blue, Green, Gold, Purple, Cyan,
  White, or Custom RGB.
- Optional **bobbing** (vertical sine-wave movement) with adjustable travel
  distance and speed.
- Optional **flashing** (opacity pulse) with adjustable speed and intensity.

**Both animation effects are disabled by default.** They can be enabled
independently. The default arrow appearance and its bone-based positioning are
unchanged. Color modes other than Original use grayscale variants of the same
cursor silhouettes; they never replace the familiar shield-shaped artwork.

## Commands

| Command | Description |
| --- | --- |
| `/ta config` | Open/close the ImGui settings window |
| `/ta status` | Show HideParty guard, drawing stage, target ID, anchor and errors |
| `/ta on` / `/ta off` / `/ta toggle` | Enable, disable, toggle TargetArrow |
| `/ta scale 1.0` | Arrow scale (0.5–2.5) |
| `/ta offset 4` | Additional upward screen offset (-100 to 150 pixels) |
| `/ta height 1.9` | World-unit height for non-skeletal fallback (0–15) |
| `/ta bob on` / `/ta bob off` | Turn vertical bobbing on/off |
| `/ta flash on` / `/ta flash off` | Turn opacity pulsing on/off |
| `/ta color blue` | Set target cursor color by name |
| `/ta subcolor purple` | Set subtarget cursor color by name |

`/targetarrow` is an alias for `/ta`. Numeric options save to local `settings.lua`; that runtime file is excluded from ZIPs and Git.

## How arrow placement works

The game provides model skeleton data independently of whether its *nameplate is shown*. TargetArrow reads the model's nameplate **bone #2** as the primary attachment coordinate—the method used in the established working TargetArrow implementation. Disabling game nameplates or using a nameplate-hiding addon therefore **should not affect placement**. The bone is transformed through the current Direct3D view/projection matrices to screen pixels.

For doors, unloaded models or unavailable skeleton information, it falls back to the entity's position plus a configurable height. **It never substitutes a low hitbox point when a valid bone is available but off-screen**, preventing the misplaced lower-right arrow seen during previous testing.

This model-bone strategy uses known client memory offsets and may require updates if the FFXI client changes. Read the [technical notes](docs/TECHNICAL.md).

## GitHub Actions ZIP builds

Two workflows are included:

- [check.yml](.github/workflows/check.yml) validates syntax, behavior tests and ZIP contents on pushes and pull requests.
- [release.yml](.github/workflows/release.yml) builds **TargetArrow-v1.0.0.zip** (installable addon) and **TargetArrow-Source-v1.0.0.zip** (GitHub source). Run it manually under **Actions → Build and Release ZIPs → Run workflow** to download build artifacts without creating a GitHub release.

When the first stable version is validated, push the Git tag `v1.0.0`; GitHub Actions then creates the release and attaches the ZIPs. No change in version numbering or a development changelog is required before stability is confirmed. See [publishing](docs/PUBLISHING.md).

## Diagnostics and validation

Use `/ta status` while facing and selecting a monster. `drawing_allowed=true` means **the HideParty guard passed**, not necessarily that a sprite was drawn. Check `last_draw=`, `anchor=` (`nameplate-bone` preferred), `draws=` and `last_error=`. If the arrow is misplaced, include these fields in an issue report.

The source and ZIPs are checked by automated tests; GUI and animation behavior still require in-game verification. The established skeleton-bone positioning is preserved, together with the HideParty guard.

## Credits and licensing

Copyright © 2026 **7h3Cub3**. This distribution is licensed **GPL-3.0-or-later**. The separate Ashita 4 runtime and original HideParty are not redistributed. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for references and the historical model-bone inspiration.

This project is not affiliated with or endorsed by Square Enix, HorizonXI, Ashita or XIUI.
