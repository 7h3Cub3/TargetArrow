# Publishing and creating ZIPs on GitHub

TargetArrow is authored by 7h3Cub3: https://github.com/7h3Cub3/TargetArrow. GPL-3.0-or-later. Version stays **1.0.0** throughout compatibility testing.

## Repository root

Put `targetarrow.lua`, `arrow.png`, `subarrow.png`, README.md, LICENSE, docs/, scripts/, tests/ and `.github/workflows/` directly in the repository root. There is **no installer**.

## Manually create ZIP artifacts while testing

In GitHub, select **Actions → Build and Release ZIPs → Run workflow**. A build ZIP and a source ZIP become downloadable workflow artifacts; there is no GitHub Release on manual runs.

You can also run `python3 scripts/package_release.py --output-dir dist` locally. The packaging script reads `addon.version` from root `targetarrow.lua` and excludes user settings, local files and backups.

## Publish first 1.0.0 only after confirmed stable

Create and push tag `v1.0.0` on the validated source. The tag workflow verifies Lua syntax, tests and ZIP contents, then creates the GitHub Release with both archives attached. Tag and embedded version must match. Do not create intermediate public release tags or a changelog series during testing.
