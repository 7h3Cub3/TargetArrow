# Implementation notes

## Why an independent arrow is required

HideParty's target primitive contains the native target HP/name window **and** the native world pointer. Its `set_primitive_visibility` code hides both. TargetArrow only draws an independently positioned Direct3D sprite, leaving the original window hidden.

## Visibility guard

The guard uses the official Ashita `AddonManager:IsLoaded('hideparty')` followed by a read-only signature lookup matching original HideParty, and checks both visibility flags (+0x69 and +0x6A) on party and target primitives. The guard runs each drawing frame and is fail-closed. It does not write to FFXI memory and cannot force HideParty to hide anything.

## Positioning and invisible nameplates

For ordinary models, the first choice is the model skeleton's **bone index 2** as its attachment point. Actor position is combined with the generator's bone offset. The 3D coordinates are projected using the Direct3D8 view and projection matrices and the current viewport. The nameplate can be hidden without changing those model coordinates. Therefore hiding nameplates generally does not affect the marker. Direct actor/skeleton offsets are client-build dependent; validate after updating the game client.

If the bone cannot be read, entity local/last coordinates are raised by the configured fallback height. An off-screen bone does not cause an entity-origin fallback, because that would misplace the marker.

## Diagnostics

`/ta status` reports whether the guard permits rendering, `last_draw`, current `target`, number of anchor `candidates`, the chosen `anchor`, successfully returned sprite submissions (`draws`), and `last_error`. A successful Direct3D draw call does not itself guarantee that a player can see the icon; only in-game observation verifies that.

## Runtime interfaces

The addon uses Ashita 4 APIs, Direct3D8 and client-specific model data. See [Third-party notices](../THIRD_PARTY_NOTICES.md) for references and attribution.

## ImGui and animation implementation

The settings panel is drawn through Ashita 4's built-in `imgui` module and triggered by `/ta config`. Its own protected event path prevents UI failures from suppressing the in-world target arrow. Sliders and toggle changes are written as plain numeric values to `settings.lua`.

At render time, optional bobbing only changes the final screen-space Y coordinate; optional flashing only changes the sprite's vertex alpha. Each effect uses a periodic function of the system tick so motion is frame-rate independent. Both default to disabled.

Default color mode chooses the original arrow/subarrow PNG with white sprite tint. Alternate colors use separately shipped neutral-luminance renderings of those same PNG silhouettes and Direct3D vertex color multiplication, so one neutral asset supports presets and custom RGB without modifying the target skeleton.
