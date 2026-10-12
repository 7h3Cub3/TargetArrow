# Packaging and publishing TargetArrow

Repository: https://github.com/7h3Cub3/TargetArrow

## Release assets

The workflow builds and publishes **only** the installable `TargetArrow-vX.Y.Z.zip`. GitHub automatically provides matching **Source code (zip)** and **Source code (tar.gz)** archives for each tag.

The text of `RELEASE_NOTES.md` is published **directly in the release description**. It is not replaced with a link or automatically generated commit notes.

## Manual build

Go to **Actions → Build and Release TargetArrow → Run workflow** to generate a `TargetArrow-Addon` artifact without publishing or editing a release.

To run the build locally:

```sh
python3 scripts/package_release.py --output-dir dist
python3 tests/test_package.py --dist-dir dist
```

## Tagged release

Push a tag such as `v1.0.0`, matching the `addon.version` field in `targetarrow.lua`. GitHub Actions builds the addon ZIP and publishes the release with the contents of `RELEASE_NOTES.md` written directly into the release body.

## Update an existing release

The release body can be refreshed directly from the checked-out repository on `main`, without changing the tag or rebuilding the binary asset:

```powershell
gh release edit v1.0.0 -R 7h3Cub3/TargetArrow --notes-file RELEASE_NOTES.md
gh release delete-asset v1.0.0 TargetArrow-Source-v1.0.0.zip -R 7h3Cub3/TargetArrow --yes
```

The installable addon archive stays attached. The standard **Source code (zip/tar.gz)** links are unaffected.
