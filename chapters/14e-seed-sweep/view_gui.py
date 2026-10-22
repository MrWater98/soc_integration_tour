#!/usr/bin/env python3
"""Open a saved Tang routed design in nextpnr's GUI, without rerunning PNR."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT/'results/14e-algorithms/best/routed.json.gz')
    parser.add_argument('--binary', type=Path, default=ROOT/'external/nextpnr-gui-viewer/build/nextpnr-himbaechel',
                        help='separate patched viewer; original OSS CAD Suite remains used for timing experiments')
    parser.add_argument('--show-nets', action='store_true', help='open Nets and show routed connections as a tile-level schematic')
    parser.add_argument('--title', default='', help='label the GUI window')
    parser.add_argument('--dry-run', action='store_true', help='prepare JSON and print command without opening a window')
    args = parser.parse_args()
    source = args.input.resolve()
    raw = gzip.decompress(source.read_bytes()) if source.suffix == '.gz' else source.read_bytes()
    summary = source.parent/'summary.json'
    if summary.exists():
        expected = json.loads(summary.read_text()).get('routed_sha256')
        if expected and hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('Routed snapshot hash mismatch')
    design = json.loads(raw)
    if len(design['modules']) != 1:
        raise ValueError('Expected a flattened routed snapshot with one module')
    top = next(iter(design['modules']))
    expanded = source.with_suffix('') if source.suffix == '.gz' else source
    if expanded != source:
        expanded.write_bytes(raw)
    binary = str(args.binary.resolve())
    if not args.binary.exists():
        parser.error('Viewer not built: run python chapters/14e-seed-sweep/build_gui_viewer.py')
    command = [binary, '--gui', '--json', str(expanded), '--top', top,
               '--device', 'GW2A-LV18PG256C8/I7', '--vopt', 'family=GW2A-18C',
               '--chipdb', str(ROOT/'external/fpga-tools/oss-cad-suite/share/nextpnr/himbaechel/gowin/chipdb-GW2A-18C.bin'),
               '--no-pack', '--no-place', '--no-route']
    print(shlex.join(command), flush=True)
    if not args.dry_run:
        environment = os.environ.copy()
        if args.show_nets: environment["NEXTPNR_VIEW_NETS"] = "1"
        if args.title: environment["NEXTPNR_VIEW_TITLE"] = args.title
        subprocess.run(command, check=True, env=environment)


if __name__ == '__main__':
    main()
