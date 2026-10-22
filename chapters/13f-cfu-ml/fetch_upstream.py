#!/usr/bin/env python3
"""Fetch only the pinned upstream checkout; do not install its entire environment."""
import json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    manifest=json.loads((HERE/'upstream/manifest.json').read_text())
    target=ROOT/'external/CFU-Playground'
    if target.exists():
        actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=target,text=True).strip()
        if actual!=manifest['commit']:raise RuntimeError(f'Existing checkout is {actual}; expected {manifest["commit"]}')
    else:
        target.mkdir(parents=True)
        subprocess.run(['git','init',str(target)],check=True)
        subprocess.run(['git','remote','add','origin',manifest['repository']],cwd=target,check=True)
        subprocess.run(['git','fetch','--depth','1','origin',manifest['commit']],cwd=target,check=True)
        subprocess.run(['git','checkout','--detach','FETCH_HEAD'],cwd=target,check=True)
    import hashlib
    for row in manifest['files']:
        for path in (target/row['upstream_path'],HERE/'upstream'/row['file']):
            if hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:raise RuntimeError(f'Hash mismatch: {path}')
    print('PASS pinned CFU Playground:',manifest['commit'])


if __name__=='__main__':main()
