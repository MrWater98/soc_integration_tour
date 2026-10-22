#!/usr/bin/env python3
"""Check actual lowered flip-flop clock pins, not module-name guesses."""
import argparse,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'results/20')
    a=p.parse_args();out=a.output.resolve()
    script=f'read_verilog {out}/rtl/generic.v\nhierarchy -check -top asic_soc\nproc\nwrite_json {out}/clock-structure.json\n'
    (out/'clock-audit.ys').write_text(script)
    r=subprocess.run(['yosys','-Q','-T','-q','-s',str(out/'clock-audit.ys')],capture_output=True,text=True,timeout=120)
    (out/'clock-audit.log').write_text(r.stdout+r.stderr);r.check_returncode()
    module=json.loads((out/'clock-structure.json').read_text())['modules']['asic_soc']
    expected=module['ports']['clk']['bits'];clocks={};types={};sequential=0
    for name,cell in module['cells'].items():
        if 'CLK' not in cell['connections']:continue
        bits=cell['connections']['CLK'];key=','.join(map(str,bits))
        clocks[key]=clocks.get(key,0)+1;types[cell['type']]=types.get(cell['type'],0)+1
        sequential+=1
        if bits!=expected:raise RuntimeError(f'Unexpected clock on {name}: {bits}')
    if sequential==0:raise RuntimeError('No sequential cells audited')
    report=dict(status='PASS all sampled storage clocks connect to top clk',
                sequential_cells=sequential,clock_pin_bits=expected,groups=clocks,cell_types=types,
                cdc_signoff='NOT_RUN: this is connectivity, not metastability or RDC analysis')
    (out/'clock-domain-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
