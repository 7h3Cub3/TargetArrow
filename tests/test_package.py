#!/usr/bin/env python3
"""Validate that release ZIPs include the required install/source files."""
from pathlib import Path
import argparse
import zipfile

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--dist-dir',type=Path,default=Path('dist'))
    args=ap.parse_args()
    version='1.0.0'
    files=[
        (f'TargetArrow-v{version}.zip',
         {f'targetarrow/{name}' for name in ('targetarrow.lua','arrow.png','subarrow.png','arrow-neutral.png','subarrow-neutral.png','LICENSE')}),
        (f'TargetArrow-Source-v{version}.zip',
         {f'TargetArrow-v{version}/{name}' for name in ('targetarrow.lua','screenshots/original-hideparty.png','screenshots/targetarrow.png','README.md','LICENSE','.github/workflows/release.yml','.github/workflows/check.yml','scripts/package_release.py','tests/test_package.py')}),
    ]
    for filename, required in files:
        path=args.dist_dir/filename
        if not path.is_file(): raise SystemExit(f'Missing ZIP: {path}')
        with zipfile.ZipFile(path) as zf:
            names=set(zf.namelist())
            if not required.issubset(names): raise SystemExit(f'ZIP missing {required-names}: {filename}')
            if zf.testzip() is not None: raise SystemExit(f'CRC failure in {filename}')
            if any('Install-TargetArrow' in name for name in names):
                raise SystemExit(f'Unexpected installer in {filename}')
            if any(name.endswith(('settings.lua','.bak')) or '__pycache__' in name for name in names):
                raise SystemExit(f'Runtime/private data in {filename}')
        print(f'OK: {path.name}')

if __name__=='__main__': main()
