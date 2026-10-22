#!/usr/bin/env python3
"""Synthesize a complete Tang Primer 20K RTL snapshot with Yosys synth_gowin."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT/'results/14-tang20k/rtl')
    parser.add_argument('--output', type=Path, default=ROOT/'results/15-tang20k')
    parser.add_argument('--top', default='tutorial14')
    parser.add_argument('--family', choices=['gw2a'], default='gw2a')
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", args.top):
        parser.error("top must be a plain Verilog identifier")
    source, out = args.input.resolve(), args.output.resolve()
    if not shutil.which('yosys'):
        parser.error('yosys not found; source tools.sh or install Yosys with Gowin technology libraries')
    if source == out/'rtl':
        parser.error('input and output RTL directories must differ')
    manifest = json.loads((source/'sources.json').read_text())
    rtl = out/'rtl'
    rtl.mkdir(parents=True, exist_ok=True)
    records = []
    for row in manifest:
        name = row['file']
        if Path(name).name != name:
            raise ValueError('source manifest must use plain filenames')
        path = source/name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != row.get('snapshot_sha256', row.get('sha256')):
            raise ValueError(f'input hash mismatch: {name}')
        shutil.copy2(path, rtl/name)
        records.append({'file': name, 'sha256': digest, 'role': row.get('role', 'design')})
    (rtl/'sources.json').write_text(json.dumps(records, indent=2)+'\n')
    files = [r['file'] for r in records if r.get('role', 'design') == 'design' and r['file'].endswith(('.v', '.sv'))]
    def quote(value):
        return '"'+value.replace('\\', '\\\\').replace('"', '\\"')+'"'
    script = '\n'.join([
        'read_verilog -sv '+' '.join(map(quote, files)),
        f'synth_gowin -family gw2a -top {args.top} -json ../netlist.json',
        'delete t:$scopeinfo',  # flatten's hierarchy metadata is not hardware
        'check -assert -noinit',
        'tee -o ../stat.json stat -json',
        'write_json ../netlist.json',
        'write_edif ../netlist.edif',
        'write_verilog -noattr ../netlist.v',
    ])+'\n'
    (out/'synth.ys').write_text(script)
    version = subprocess.check_output(['yosys', '-V'], text=True).strip()
    with (out/'console.log').open('w') as stream:
        proc = subprocess.run(['yosys', '-l', str(out/'synthesis.log'), '-s', str(out/'synth.ys')], cwd=rtl, stdout=stream, stderr=subprocess.STDOUT)
    if proc.returncode:
        raise RuntimeError(f'synthesis failed; inspect {out / "synthesis.log"}')
    netlist = json.loads((out/'netlist.json').read_text())
    cells = collections.Counter(c['type'] for c in netlist['modules'][args.top]['cells'].values())
    unresolved = [name for name in cells if name.startswith('$')]
    if unresolved:
        raise RuntimeError(f'unmapped internal cells: {unresolved}')
    if args.family=='gw2a' and not cells.get('rPLL'):
        raise RuntimeError('Gowin PLL disappeared')
    for name in ['netlist.json', 'netlist.edif', 'netlist.v']:
        if (out/name).stat().st_size == 0:
            raise RuntimeError(f'empty output: {name}')
    summary = dict(synthesis='PASS', family=args.family, top=args.top, yosys=version, cells=dict(sorted(cells.items())),
                   placement_routing='NOT_RUN', timing='NOT_RUN', bitstream='NOT_RUN', onboard='SKIP')
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    report = ['# 第 15 章：开源 FPGA 综合', '', f'PASS：完整 SoC 已映射到 {args.family} 原语；check -assert 通过。', '', version, '', '| 原语 | 数量 |', '| --- | ---: |']
    report += [f'| {name} | {count} |' for name, count in sorted(cells.items())]
    report += ['', '布局布线、时序与 bitstream：NOT_RUN；上板：SKIP。', '资源数来自综合网表，不是布局布线后的资源占用或时序结论。']
    (out/'REPORT.md').write_text('\n'.join(report)+'\n')
    print(f'PASS 15 synthesis: {sum(cells.values())} mapped cells; {out}; place/route and bitstream NOT_RUN')


if __name__ == '__main__':
    main()
