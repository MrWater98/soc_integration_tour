#!/usr/bin/env python3
"""Check imported files and Python syntax; report tools without running hardware."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ('iverilog', 'vvp', 'verilator', 'verilator_coverage', 'yosys',
         'riscv64-unknown-elf-gcc', 'nextpnr-himbaechel', 'gowin_pack',
         'openFPGALoader', 'openocd', 'gdb', 'sta')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Also save the JSON report')
    parser.add_argument('--require-tools', action='store_true',
                        help='Fail if any listed tool is unavailable')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'docs/progress/sync-manifest.json').read_text())
    errors = []
    python_count = 0
    for row in manifest['files']:
        path = ROOT / row['path']
        if not path.is_file():
            errors.append(f'Missing file: {row["path"]}')
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            errors.append(f'Changed since import: {row["path"]}')
        if path.suffix == '.py':
            python_count += 1
            try:
                ast.parse(path.read_text(), filename=str(path))
            except SyntaxError as exc:
                errors.append(str(exc))
    init_references = 0
    for path in (ROOT / 'results').glob('*/rtl/**/*'):
        if not path.is_file() or path.suffix not in ('.v', '.sv'):
            continue
        for name in re.findall(r'\$readmem[hb]\s*\(\s*"([^"]+)"', path.read_text(errors='replace')):
            init_references += 1
            if not (path.parent / name).is_file():
                errors.append(f'Missing initialization file: {path.relative_to(ROOT)} -> {name}')
    tools = {}
    for name in TOOLS:
        local = ROOT / 'external/fpga-tools/oss-cad-suite/bin' / name
        tools[name] = str(local) if local.is_file() else shutil.which(name)
    if args.require_tools:
        errors.extend(f'Missing tool: {name}' for name, path in tools.items() if not path)
    result = {
        'status': 'FAIL' if errors else 'PASS file integrity and Python syntax',
        'files_checked': len(manifest['files']), 'python_files_checked': python_count,
        'literal_memory_initialization_references': init_references,
        'tools': tools, 'pdk_present': (ROOT / 'external/icsprout55-pdk').is_dir(),
        'errors': errors,
        'scope': 'No simulation, synthesis, dependency install, or board access performed',
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end='')
    sys.exit(bool(errors))


if __name__ == '__main__':
    main()
