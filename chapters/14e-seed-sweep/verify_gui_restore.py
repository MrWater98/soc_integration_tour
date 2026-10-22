#!/usr/bin/env python3
"""Verify that the patched loader restores all saved BELs and routed resources."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
binary = ROOT/'external/nextpnr-gui-viewer/build/nextpnr-himbaechel'
snapshot = ROOT/'results/14e-algorithms/best/routed.json.gz'
out = ROOT/'results/14e-gui'
out.mkdir(parents=True, exist_ok=True)
raw = gzip.decompress(snapshot.read_bytes())


def placements(module):
    return {name: cell['attributes']['NEXTPNR_BEL'] for name, cell in module['cells'].items()
            if 'NEXTPNR_BEL' in cell.get('attributes', {})}


def routes(module):
    result = {}
    for name, net in module['netnames'].items():
        text = net.get('attributes', {}).get('ROUTING', '').strip()
        if text:
            tokens = text.split(';')
            assert len(tokens) % 3 == 0
            result[name] = frozenset(tuple(tokens[i:i+3]) for i in range(0, len(tokens), 3))
    return result


with tempfile.TemporaryDirectory(prefix='nextpnr-restore-') as temporary:
    directory = Path(temporary)
    (directory/'input.json').write_bytes(raw)
    (directory/'check.py').write_text("print('RESTORED_CONTEXT_LOADED')\n")
    command = [str(binary), '--json', str(directory/'input.json'), '--top', 'top',
               '--device', 'GW2A-LV18PG256C8/I7', '--vopt', 'family=GW2A-18C',
               '--chipdb', str(ROOT/'external/fpga-tools/oss-cad-suite/share/nextpnr/himbaechel/gowin/chipdb-GW2A-18C.bin'),
               '--run', str(directory/'check.py'), '--write', str(directory/'restored.json')]
    with (out/'restore.log').open('w') as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=45)
    before = json.loads(raw)['modules']['top']
    after = json.loads((directory/'restored.json').read_text())['modules']['top']
    assert placements(before) == placements(after), 'Placement changed during restore'
    assert routes(before) == routes(after), 'Routing changed during restore'
    summary = {'status': 'PASS', 'snapshot_sha256': hashlib.sha256(raw).hexdigest(),
               'placed_cells': len(placements(before)), 'nonempty_routed_nets': len(routes(before)),
               'routing_resource_triples': sum(map(len, routes(before).values())),
               'verification': 'read saved JSON into actual nextpnr context and export it; compare all BEL positions and per-net route triples',
               'empty_route_normalization': 'blank/space-only ROUTING attributes represent no routing',
               'rerun_placement_routing': False}
    (out/'restore-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print('PASS:', summary['placed_cells'], 'placements;', summary['nonempty_routed_nets'], 'routed nets')
