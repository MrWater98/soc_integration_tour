#!/usr/bin/env python3
"""Frozen-core regression, targeted faults, bounded properties and line coverage."""
import argparse,hashlib,json,re,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
TOOLS = ROOT/'external/fpga-tools/oss-cad-suite/bin'
IVERILOG = str(TOOLS/'iverilog') if (TOOLS/'iverilog').exists() else 'iverilog'
VVP = str(TOOLS/'vvp') if (TOOLS/'vvp').exists() else 'vvp'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=ROOT/'results/19/rtl')
    p.add_argument('--output',type=Path,default=ROOT/'results/20')
    p.add_argument('--boots',type=int,default=8)
    a=p.parse_args()
    if a.boots<2: p.error('At least two reset/reboot iterations required')
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    (out/'summary.json').unlink(missing_ok=True)
    rtl=out/'rtl';rtl.mkdir(exist_ok=True)
    for f in a.input.resolve().iterdir():
        if f.suffix in ('.v','.init'):shutil.copyfile(f,rtl/f.name)
    if not (rtl/'elaborated.v').exists():raise RuntimeError('Run chapter 19 first')
    results=[]
    def run(cmd,name,expected=None,fail=False,timeout=300,cwd=None):
        r=subprocess.run(list(map(str,cmd)),cwd=cwd or rtl,capture_output=True,text=True,timeout=timeout)
        text=r.stdout+r.stderr;(out/name).write_text(text)
        ok=(expected in text if expected else r.returncode==0)
        if not fail:ok=ok and r.returncode==0 and 'FATAL:' not in text
        if not ok:raise RuntimeError(f'{name}: unexpected result (return={r.returncode})')
        return text
    run([IVERILOG,'-g2012','-DRTL_FAULTS','-s','tb','-o',out/'rtl.vvp',rtl/'elaborated.v',HERE/'tb.sv'],'compile.log')
    def sim(name,args,expected,fail=False):
        text=run([VVP,out/'rtl.vvp',*args],f'{name}.log',expected,fail=fail)
        results.append(dict(name=name,status='PASS expected failure detected' if fail else 'PASS',
                            arguments=args,expected=expected))
    sim('cold',[],'PASS20')
    sim('repeated-reset',[f'+BOOTS={a.boots}'],'PASS20')
    sim('reset-during-ram',['+RESET_STAGE=2'],'PASS20')
    sim('reset-before-timer',['+RESET_STAGE=5'],'PASS20')
    sim('fault-ram-data',['+FAULT=1'],'FIRMWARE_FAIL result=000000e1',True)
    sim('fault-no-ack',['+FAULT=2'],'WATCHDOG',True)
    sim('fault-irq-masked',['+FAULT=3'],'WATCHDOG',True)
    sim('fault-gpio',['+FAULT=4'],'FIRMWARE_FAIL result=000000e5',True)
    for netlist in ('generic','mapped'):
        if not (rtl/f'{netlist}.v').exists():raise RuntimeError(f'Missing {netlist} snapshot from chapter 19')
        sources=[rtl/f'{netlist}.v']
        if netlist=='mapped':sources+=[rtl/'ics55_LLSC_H7CR.v']
        run([IVERILOG,'-g2012','-Dfunctional','-s','tb','-o',out/f'{netlist}.vvp',*sources,HERE/'tb.sv'],f'{netlist}-compile.log')
        run([VVP,out/f'{netlist}.vvp','+BOOTS=2'],f'{netlist}-run.log','PASS20')
        results.append(dict(name=f'{netlist}-cold-and-warm',status='PASS'))
    run([IVERILOG,'-g2012','-s','tb','-o',out/'reset.vvp',rtl/'reset_sync.v',HERE/'reset_tb.sv'],'reset-compile.log')
    run([VVP,out/'reset.vvp'],'reset-phase.log','PASS_RESET')
    run([IVERILOG,'-g2012','-s','tb','-o',out/'stress.vvp',rtl/'peripheral.v',HERE/'stress_tb.sv'],'stress-compile.log')
    for seed in (1,7,19):
        text=run([VVP,out/'stress.vvp',f'+SEED={seed}','+COUNT=10000'],f'stress-{seed}.log','PASS_STRESS')
        counts=re.search(r'requests=(\d+) reset_aborts=(\d+)',text)
        if not counts:raise RuntimeError('Missing stress transaction counts')
        requests,aborts=map(int,counts.groups())
        results.append(dict(name=f'peripheral-random-{seed}',status='PASS',requests=requests,
                            reset_aborts=aborts,completed=requests-aborts,functional_bins='20/20'))
    lint=run(['verilator','--lint-only','-Wno-fatal','--top-module','asic_soc',
              rtl/'asic_soc.v',rtl/'VexRiscv_Min.v',rtl/'reset_sync.v',rtl/'peripheral.v'],'lint.log')
    warnings={}
    for tag in re.findall(r'%Warning-([A-Z0-9_]+)',lint):warnings[tag]=warnings.get(tag,0)+1
    for tag in ('LATCH','MULTIDRIVEN','UNOPTFLAT'):
        if tag in warnings:raise RuntimeError(f'Blocking lint warning {tag}')
    unknown_warnings=set(warnings)-{'WIDTHEXPAND','WIDTHTRUNC','CASEINCOMPLETE'}
    if unknown_warnings:raise RuntimeError(f'Unreviewed lint warnings: {unknown_warnings}')
    run([sys.executable,HERE/'clock_audit.py','--output',out],'clock-audit-run.log','PASS')
    # Bounded proof: arbitrary inputs over 12 cycles, initial reset assumed.
    formal=f'''read_verilog -formal -sv {rtl}/peripheral.v {HERE}/properties.sv
prep -top properties -flatten
async2sync
chformal -lower
sat -seq 12 -prove-asserts -set-assumes -verify
'''
    (out/'properties.ys').write_text(formal)
    run(['yosys','-s',out/'properties.ys'],'formal.log','SUCCESS')
    mutant=(rtl/'peripheral.v').read_text().replace('assign ack = request && response_ready;', 'assign ack = response_ready;')
    if mutant==(rtl/'peripheral.v').read_text():raise RuntimeError('Mutation did not apply')
    (out/'bad_ack.v').write_text(mutant)
    (out/'negative-properties.ys').write_text(formal.replace(str(rtl/'peripheral.v'),str(out/'bad_ack.v')))
    run(['yosys','-s',out/'negative-properties.ys'],'formal-negative.log','proof did fail',True)
    run([sys.executable,HERE/'coverage.py','--output',out],'coverage-driver.log','lines_hit')
    coverage=json.loads((out/'coverage-summary.json').read_text())
    summary=dict(status='PASS implemented checks; production freeze OPEN',cases=results,
        repeated_boots=a.boots,lint_warning_counts=warnings,
        formal='PASS 12-step bounded safety checks; ACK mutation rejected',
        reset='PASS async assertion/two-edge release at nine phase trials',
        clock_connectivity=json.loads((out/'clock-domain-audit.json').read_text()),
        cdc='structural review + simulation only; no dedicated CDC/RDC signoff',
        coverage=coverage,
        equivalence='NOT_RUN full sequential equivalence; RTL/generic/ICS55 directed regressions passed',
        remaining=['uncovered CPU instructions/branches','full CDC/RDC tool review','multi-corner gate timing','long-duration stress signoff','pad-ring/physical verification'])
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (rtl/'sources.json').write_text(json.dumps(dict(files=[dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted(rtl.iterdir()) if f.suffix in ('.v','.init')]),indent=2)+'\n')
    (out/'REPORT.md').write_text('# 20 验证工作包结果\n\n'+summary['status']+'\n\n| 案例 | 状态 |\n| --- | --- |\n'+''.join('| '+case['name']+' | '+case['status']+' |\n' for case in results)+'\n纯行覆盖和时钟连接详见coverage-summary.json、clock-domain-audit.json；具体缺项见summary.json。\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
