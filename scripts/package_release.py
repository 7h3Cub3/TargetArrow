#!/usr/bin/env python3
"""Build the reproducible, version-matched installable TargetArrow addon ZIP.

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
    # A patch-zero addon version (1.0.0) is released as tag 1.0.
    # Nonzero patch versions use the full tag (1.0.1, etc.).
    major, minor, patch = (int(part) for part in version.split('.'))
    expected = f'{major}.{minor}' if patch == 0 else f'{major}.{minor}.{patch}'
    if tag is not None and tag != expected:
        raise ValueError(f'Tag {tag!r} does not match addon.version ({expected})')
    outdir.mkdir(parents=True, exist_ok=True)
    addon_zip = outdir / f'TargetArrow-{expected}.zip'
    # Ensure the output contains no redundant source archive.
    legacy_source = outdir / f'TargetArrow-Source-{expected}.zip'
    if legacy_source.exists():
        legacy_source.unlink()

    for file in ADDON_FILES:
        if not (ROOT / file).is_file():
            raise FileNotFoundError(file)
    if not (ROOT / 'LICENSE').is_file():
        raise FileNotFoundError('LICENSE')

    with zipfile.ZipFile(addon_zip, 'w') as zf:
        for name in ADDON_FILES:
            pack_file(zf, ROOT / name, f'targetarrow/{name}')
        pack_file(zf, ROOT / 'LICENSE', 'targetarrow/LICENSE')

    return (addon_zip,)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist')
    parser.add_argument('--tag', help='Release tag, must match the embedded addon version (1.0.0 -> 1.0)')
    args = parser.parse_args()
    try:
        files = build(args.output_dir, args.tag)
    except (ValueError, FileNotFoundError) as error:
        parser.error(str(error))
    for file in files:
        print(file)


if __name__ == '__main__':
    main()
