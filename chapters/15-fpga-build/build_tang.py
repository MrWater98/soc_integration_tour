#!/usr/bin/env python3
"""Place/route a verified GW2A netlist and pack the Tang Primer 20K bitstream."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
DEVICE='GW2A-LV18PG256C8/I7'
FAMILY='GW2A-18C'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--synthesis',type=Path,default=ROOT/'results/15-tang20k')
    parser.add_argument('--platform',type=Path,default=ROOT/'results/14-tang20k')
    parser.add_argument('--output',type=Path,default=ROOT/'results/15-tang20k-build')
    parser.add_argument('--seed',type=int,default=1)
    args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True);(out/'summary.json').unlink(missing_ok=True)
    synth=json.loads((args.synthesis/'summary.json').read_text())
    manifest=json.loads((args.platform/'manifest.json').read_text())
    if synth['synthesis']!='PASS' or synth['family']!='gw2a':raise ValueError('need successful GW2A synthesis')
    if manifest['device']!=DEVICE or manifest['family']!=FAMILY:raise ValueError('wrong board device')
    # Never combine a fresh platform configuration with an older compiled ROM/RTL.
    synth_sources=json.loads((args.synthesis/'rtl/sources.json').read_text())
    platform_sources={r['file']:r['snapshot_sha256'] for r in manifest['sources']}
    for row in synth_sources:
        if row['sha256']!=platform_sources[row['file']]:raise ValueError(f'platform/synthesis mismatch: {row["file"]}')
    nextpnr=shutil.which('nextpnr-himbaechel');packer=shutil.which('gowin_pack')
    if not nextpnr or not packer:raise RuntimeError('activate OSS CAD Suite; nextpnr-himbaechel/gowin_pack missing')
    shutil.copy2(args.synthesis/'netlist.json',out/'netlist.json')
    shutil.copy2(args.platform/'constraints/tutorial14.cst',out/'tutorial14.cst')
    frequency=max(manifest['config']['reference_clk_hz'],manifest['config']['sys_clk_hz'])/1e6
    command=[nextpnr,'--json','netlist.json','--write','routed.json','--report','pnr-report.json',
             '--top',synth['top'],'--device',DEVICE,'--vopt',f'family={FAMILY}',
             '--vopt','cst=tutorial14.cst','--freq',str(frequency),'--seed',str(args.seed)]
    # Deliberately no --timing-allow-fail: a violated target must stop the build.
    pack=[packer,'-d',FAMILY,'-o','tutorial14.fs','--ready_as_gpio','--done_as_gpio','routed.json']
    (out/'commands.json').write_text(json.dumps([command,pack],indent=2)+'\n')
    version=subprocess.run([nextpnr,'--version'],capture_output=True,text=True,check=True)
    with (out/'nextpnr.log').open('w') as stream:
        run=subprocess.run(command,cwd=out,stdout=stream,stderr=subprocess.STDOUT)
    if run.returncode:raise RuntimeError(f'place/route or timing failed; inspect {out/"nextpnr.log"}')
    report=json.loads((out/'pnr-report.json').read_text())
    clocks=report.get('fmax',{})
    if 'VexRiscv.clk' not in clocks:raise RuntimeError('CPU clock missing from timing report')
    for name,clock in clocks.items():
        if clock['constraint']<frequency or clock['achieved']<clock['constraint']:raise RuntimeError(f'unsatisfied/missing target for {name}: {clock}')
    with (out/'pack.log').open('w') as stream:
        packed=subprocess.run(pack,cwd=out,stdout=stream,stderr=subprocess.STDOUT)
    if packed.returncode:raise RuntimeError(f'packing failed; inspect {out/"pack.log"}')
    data=(out/'tutorial14.fs').read_bytes()
    if not data:raise RuntimeError('empty bitstream')
    summary=dict(placement_routing='PASS',timing='PASS: nextpnr accepted requested clock target',bitstream='PASS',
                 onboard='SKIP: board not delivered',device=DEVICE,family=FAMILY,seed=args.seed,
                 target_mhz=frequency,nextpnr_version=(version.stdout+version.stderr).strip(),
                 bitstream_bytes=len(data),bitstream_sha256=hashlib.sha256(data).hexdigest(),report=report)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    resource_table='\n'.join(f'| {name} | {row["used"]} | {row["available"]} |' for name,row in report['utilization'].items() if name in ('LUT4','DFF','BSRAM','MULT18X18','ALU'))
    (out/'REPORT.md').write_text(f'# Tang Primer 20K：开源构建\n\nPASS：布局布线、nextpnr 目标 {frequency:g} MHz 检查、bitstream 生成。\n\n器件 `{DEVICE}`，family `{FAMILY}`，seed {args.seed}。\n\nbitstream {len(data)} bytes，SHA256 `{summary["bitstream_sha256"]}`。\n\n| 资源 | 实际使用 | 可用 |\n| --- | ---: | ---: |\n{resource_table}\n\n实际资源/时钟见 `summary.json` 的 report；原始日志 `nextpnr.log`。该检查不是 ASIC 签核；上板 SKIP，尚未拿到板子。\n')
    print(f'PASS Tang20K build: {len(data)} bytes; timing target {frequency:g} MHz; onboard SKIP')

if __name__=='__main__':main()
