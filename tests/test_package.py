#!/usr/bin/env python3
"""Validate that the single installable release ZIP includes the required addon files."""
from pathlib import Path
import argparse
import zipfile

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--dist-dir',type=Path,default=Path('dist'))
    args=ap.parse_args()
    tag='1.0'
    files=[
        (f'TargetArrow-{tag}.zip',
         {f'targetarrow/{name}' for name in ('targetarrow.lua','arrow.png','subarrow.png','arrow-neutral.png','subarrow-neutral.png','LICENSE')}),
    ]
    extras={path.name for path in args.dist_dir.glob('*.zip')} - {files[0][0]}
    if extras:
        raise SystemExit(f'Unexpected extra ZIPs: {sorted(extras)}')
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
