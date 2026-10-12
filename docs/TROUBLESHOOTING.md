# Troubleshooting

- `drawing_allowed=false`: load stock HideParty and run `/hideparty hide`; make sure the native **party and target** windows disappear. Original target arrow disappears too—TargetArrow replaces it.
- `drawing_allowed=true` but no arrow: target an NPC or monster, face it, run `/ta status` and inspect `last_draw`, `anchor`, `draws`, `last_error`.
- `anchor=nameplate-bone`: the model skeleton supplied an attachment coordinate. The arrow should be above its head, even with nameplates turned off.
- `anchor=entity-fallback`: the model bone could not be found. Use `/ta height` if its icon is too low; this setting never alters positions when the skeleton bone is available.
- `last_draw=target outside viewport`: check camera orientation. A model can be selected but not in view.
- `/hideparty show` causes the replacement arrow to disappear: expected; prevents overlapping original and replacement pointers.
- `Draw error`: copy the complete console line and attach it to an issue at https://github.com/7h3Cub3/TargetArrow/issues.

Use `/addon reload targetarrow` after changing Lua files. TargetArrow does not hide frames; HideParty does.
