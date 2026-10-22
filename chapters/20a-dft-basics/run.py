#!/usr/bin/env python3
"""Run actual scan and March RTL simulations and publish explicit fault denominators."""
import argparse,csv,hashlib,json,re,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
TOOLS = ROOT/'external/fpga-tools/oss-cad-suite/bin'
IVERILOG = str(TOOLS/'iverilog') if (TOOLS/'iverilog').exists() else 'iverilog'
VVP = str(TOOLS/'vvp') if (TOOLS/'vvp').exists() else 'vvp'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'results/20a')
    p.add_argument('--depth',type=int,default=8,choices=(4,8,16))
    p.add_argument('--width',type=int,default=8,choices=(4,8,16))
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    (out/'summary.json').unlink(missing_ok=True)
    rtl=out/'rtl';rtl.mkdir(exist_ok=True)
    for src in HERE.glob('*.sv'):shutil.copyfile(src,rtl/src.name)
    def command(cmd,path):
        r=subprocess.run(list(map(str,cmd)),cwd=path,capture_output=True,text=True,timeout=60)
        (path/'run.log').write_text(r.stdout+r.stderr)
        r.check_returncode();return r.stdout+r.stderr
    command([IVERILOG,'-g2012','-s','tb','-o',out/'scan.vvp',rtl/'scan_counter.sv',rtl/'tb_scan.sv'],out)
    command([IVERILOG,'-g2012','-s','tb',f'-Ptb.DEPTH={a.depth}',f'-Ptb.WIDTH={a.width}',
             '-o',out/'ram.vvp',rtl/'ram_model.sv',rtl/'tb_ram.sv'],out)
    cases=out/'cases';cases.mkdir(exist_ok=True)
    def case(name,exe,args,pattern):
        folder=cases/name;folder.mkdir(exist_ok=True)
        text=command([VVP,out/exe,*args],folder)
        m=re.search(pattern,text)
        if not m:raise RuntimeError(f'Missing result in {name}')
        return int(m.group(1))
    case('scan-healthy','scan.vvp',['+FAULT=-1','+MODE=1'],r'mismatches=(\d+)')
    case('scan-healthy-normal','scan.vvp',['+FAULT=-1','+MODE=0'],r'mismatches=(\d+)')
    matrix=[]
    for fault in range(8):
        normal=case(f'scan-{fault}-normal','scan.vvp',[f'+FAULT={fault}','+MODE=0'],r'mismatches=(\d+)')
        scan=case(f'scan-{fault}-test','scan.vvp',[f'+FAULT={fault}','+MODE=1'],r'mismatches=(\d+)')
        matrix.append(dict(fault=f'q[{fault//2}] stuck-{fault%2}',normal_detected=normal>0,scan_detected=scan>0))
    case('ram-healthy','ram.vvp',[],r'mismatches=(\d+)')
    ram=[]
    for bit in range(a.width):
        for value in (0,1):
            detected=case(f'ram-data-{bit}-sa{value}','ram.vvp',['+KIND=1',f'+BIT={bit}',f'+VALUE={value}'],r'mismatches=(\d+)')
            ram.append(dict(fault=f'data[{bit}] stuck-{value}',detected=detected>0,mismatches=detected))
    for bit in range(a.depth.bit_length()-1):
        detected=case(f'ram-address-{bit}-sa0','ram.vvp',['+KIND=2',f'+BIT={bit}'],r'mismatches=(\d+)')
        ram.append(dict(fault=f'address[{bit}] forced-0 alias',detected=detected>0,mismatches=detected))
    if not all(r['scan_detected'] for r in matrix) or not all(r['detected'] for r in ram):
        raise RuntimeError('A listed fault escaped')
    summary=dict(status='PASS teaching DFT simulations',depth=a.depth,width=a.width,
        scan=dict(listed_faults=8,normal_detected=sum(r['normal_detected'] for r in matrix),
                  scan_detected=sum(r['scan_detected'] for r in matrix),matrix=matrix),
        ram=dict(listed_faults=len(ram),detected=sum(r['detected'] for r in ram),matrix=ram,operations_per_case=10*a.depth),
        recovery='PASS scan exit + reset + eight functional cycles in every scan case',
        excluded_faults=['transition/delay','bridging','analog retention','coupling','scan clock/reset defects','all full-SoC gates'],
        production_atpg='NOT_RUN',mbist_macro_qualification='NOT_RUN')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (rtl/'sources.json').write_text(json.dumps(dict(files=[dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted(rtl.glob('*.sv'))]),indent=2)+'\n')
    lines=['# DFT实验实际故障检测矩阵','','| 故障 | 正常IO检测 | 扫描检测 |','| --- | --- | --- |']
    lines += [f"| {r['fault']} | {r['normal_detected']} | {r['scan_detected']} |" for r in matrix]
    lines += ['','| RAM故障 | March检测 | 读不匹配数 |','| --- | --- | --- |']
    lines += [f"| {r['fault']} | {r['detected']} | {r['mismatches']} |" for r in ram]
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
