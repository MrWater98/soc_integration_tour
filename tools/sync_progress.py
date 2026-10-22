#!/usr/bin/env python3
"""Import tutorial stages 13–20A without changing the tour's existing 00–12."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RENAMES = {
    '01-single-vex': '01-cpu-bringup',
    '05-decode': '05-memory-map',
    '06-soc': '06-litex-soc',
}


def stage(name: str) -> int | None:
    match = re.match(r'^(\d+)(?:[a-z])?(?:-|$)', name)
    return int(match[1]) if match else None


def selected(path: Path) -> bool:
    parts = path.parts
    if parts[0] in ('chapters', 'results') and len(parts) > 1:
        number = stage(parts[1])
        return number is not None and 13 <= number <= 20
    if parts[0] == 'docs':
        return True
    if parts[0] == 'instructor' and len(parts) > 2:
        number = stage(path.stem)
        return number is not None and 13 <= number <= 20
    return str(path) in ('PLAN.md', 'tutorial_paths.py')


def content(source: Path, relative: Path) -> bytes:
    data = (source / relative).read_bytes()
    # Source/docs get local paths. Historical logs, manifests and RTL remain exact.
    if relative.suffix == '.md' and relative.parts[0] != 'results':
        text = data.decode('utf-8').replace('soc_integration_tutorial/', 'soc_integration_tour/')
        for old, new in RENAMES.items():
            text = text.replace(f'chapters/{old}', f'chapters/{new}')
        if str(relative) == 'PLAN.md':
            text = ('> tour 同步说明：本计划引入 tutorial 的完整路线与进度。'
                    'tour 原有 00–12 章保持原样，表中这些章节的历史验收尚未逐项重跑；'
                    '13–20A 的同步范围及本地验收见 [进度说明](docs/progress/README.md)。\n\n' + text)
        return text.encode('utf-8')
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT.parent / 'soc_integration_tutorial')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true', help='Copy selected files and record provenance')
    mode.add_argument('--check', action='store_true', help='Fail if selected files differ or are missing')
    args = parser.parse_args()
    source = args.source.resolve()
    if source == ROOT or not (source / '.git').exists():
        parser.error('--source must point to the separate tutorial Git checkout')
    listing = subprocess.run(
        ['git', '-C', str(source), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
        check=True, capture_output=True,
    ).stdout
    paths = sorted({Path(p.decode()) for p in listing.split(b'\0') if p})
    files = [p for p in paths if selected(p) and (source / p).is_file()]
    changed = []
    records = []
    for relative in files:
        data = content(source, relative)
        destination = ROOT / relative
        if not destination.is_file() or destination.read_bytes() != data:
            changed.append(str(relative))
            if args.apply:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
                destination.chmod((source / relative).stat().st_mode & 0o777)
        records.append({'path': str(relative), 'bytes': len(data),
                        'sha256': hashlib.sha256(data).hexdigest()})
    if args.apply:
        # Result inclusion rules are shared; existing tour results remain untouched.
        (ROOT / '.gitignore').write_bytes((source / '.gitignore').read_bytes())
        revision = subprocess.run(['git', '-C', str(source), 'rev-parse', 'HEAD'],
                                  check=True, capture_output=True, text=True).stdout.strip()
        status = subprocess.run(['git', '-C', str(source), 'status', '--porcelain'],
                                check=True, capture_output=True, text=True).stdout
        manifest = {'source': 'soc_integration_tutorial', 'source_head': revision,
                    'source_dirty': bool(status), 'scope': '13–20A, docs, PLAN, path helper',
                    'historical_results': 'Copied evidence; not a fresh execution in tour',
                    'files': records}
        report = ROOT / 'docs/progress/sync-manifest.json'
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'mode': 'apply' if args.apply else 'check' if args.check else 'preview',
                      'files': len(files), 'bytes': sum(r['bytes'] for r in records),
                      'changed': len(changed), 'examples': changed[:12]},
                     ensure_ascii=False, indent=2))
    if args.check and changed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
