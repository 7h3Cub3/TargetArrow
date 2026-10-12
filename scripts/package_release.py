#!/usr/bin/env python3
"""Build reproducible, version-matched ZIP releases for the TargetArrow addon.

The archive layout is deliberately compatible with "Extract here" into Game/addons:
    targetarrow/targetarrow.lua
    targetarrow/arrow.png
    targetarrow/subarrow.png
    targetarrow/arrow-neutral.png
    targetarrow/subarrow-neutral.png
    targetarrow/LICENSE
No userdata, settings or local backups are copied.
"""
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / 'targetarrow.lua'
ADDON_FILES = ('targetarrow.lua', 'arrow.png', 'subarrow.png', 'arrow-neutral.png', 'subarrow-neutral.png')


def read_version():
    match = re.search(r"^addon\.version\s*=\s*['\"](\d+\.\d+\.\d+)['\"]", METADATA.read_text(encoding='utf-8'), re.M)
    if not match:
        raise ValueError('Cannot read semantic version from targetarrow.lua')
    return match.group(1)


def pack_file(zf, path, archive_name):
    """Write canonical archive paths and fixed timestamps for reproducibility."""
    content = path.read_bytes()
    meta = zipfile.ZipInfo(archive_name, date_time=(2026, 1, 1, 0, 0, 0))
    meta.compress_type = zipfile.ZIP_DEFLATED
    meta.external_attr = (0o100644 & 0xFFFF) << 16
    zf.writestr(meta, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build(outdir, tag=None):
    version = read_version()
    expected = f'v{version}'
    if tag is not None and tag != expected:
        raise ValueError(f'Tag {tag!r} does not match addon.version ({expected})')
    outdir.mkdir(parents=True, exist_ok=True)
    addon_zip = outdir / f'TargetArrow-v{version}.zip'
    source_zip = outdir / f'TargetArrow-Source-v{version}.zip'

    for file in ADDON_FILES:
        if not (ROOT / file).is_file():
            raise FileNotFoundError(file)
    if not (ROOT / 'LICENSE').is_file():
        raise FileNotFoundError('LICENSE')

    with zipfile.ZipFile(addon_zip, 'w') as zf:
        for name in ADDON_FILES:
            pack_file(zf, ROOT / name, f'targetarrow/{name}')
        pack_file(zf, ROOT / 'LICENSE', 'targetarrow/LICENSE')

    # Explicitly select repository-owned source files; exclude runtime settings,
    # backup directories, caches, build output and any accidental local secrets.
    tracked = [
        '.gitattributes', '.gitignore',
        'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md',
    ]
    paths = [ROOT / name for name in tracked + list(ADDON_FILES)]
    for folder in ('docs', 'tests', 'scripts', 'screenshots', '.github/workflows'):
        paths.extend(p for p in (ROOT / folder).rglob('*') if p.is_file() and not p.name.endswith(('.pyc', '.bak')) and '__pycache__' not in p.parts)
    with zipfile.ZipFile(source_zip, 'w') as zf:
        for file in sorted(set(paths), key=lambda x: x.relative_to(ROOT).as_posix()):
            if not file.is_file():
                raise FileNotFoundError(file)
            pack_file(zf, file, f'TargetArrow-v{version}/{file.relative_to(ROOT).as_posix()}')
    return addon_zip, source_zip


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist')
    parser.add_argument('--tag', help='Release tag, required to match the embedded version exactly')
    args = parser.parse_args()
    try:
        files = build(args.output_dir, args.tag)
    except (ValueError, FileNotFoundError) as error:
        parser.error(str(error))
    for file in files:
        print(file)


if __name__ == '__main__':
    main()
