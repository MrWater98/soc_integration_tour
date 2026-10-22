#!/usr/bin/env python3
"""Collect line-only coverage; do not mix signal toggles into the line denominator."""
import argparse,json,re,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'results/20')
    a=p.parse_args();out=a.output.resolve();rtl=out/'rtl'
    def run(command,name,cwd=rtl):
        r=subprocess.run(list(map(str,command)),cwd=cwd,capture_output=True,text=True,timeout=600)
        (out/name).write_text(r.stdout+r.stderr);r.check_returncode();return r.stdout+r.stderr
    run(['verilator','--cc','--exe','--build','-j','2','--coverage-line','-Wno-fatal',
         '--top-module','asic_soc','--Mdir',out/'coverage-line-obj',
         rtl/'asic_soc.v',rtl/'VexRiscv_Min.v',rtl/'reset_sync.v',rtl/'peripheral.v',HERE/'coverage.cpp'],
        'coverage-build.log')
    text=run([out/'coverage-line-obj/Vasic_soc',out/'coverage.dat'],'coverage-run.log')
    if 'result=5a' not in text:raise RuntimeError('Coverage run failed firmware checks')
    annotation=run(['verilator_coverage','--annotate-min','1','--annotate',out/'annotated',
         '--write-info',out/'coverage.info',out/'coverage.dat'],'coverage-report.log',cwd=out)
    info=(out/'coverage.info').read_text()
    counts=[int(x) for x in re.findall(r'^DA:\d+,(\d+)',info,re.M)]
    if not counts:raise RuntimeError('No line coverage data')
    hit=sum(n>0 for n in counts)
    strict=re.search(r'Total coverage \((\d+)/(\d+)\)',annotation)
    if not strict:raise RuntimeError('Missing annotation coverage counts')
    all_hit,all_total=map(int,strict.groups())
    summary=dict(all_points_hit_lines=all_hit,annotation_lines=all_total,
                 all_points_hit_percent=100*all_hit/all_total,mode='Verilator --coverage-line; annotate minimum 1',lines_hit=hit,
                 lines_total=len(counts),percent=100*hit/len(counts),
                 scope='instrumented source lines in one firmware run, includes CPU; no toggle counters')
    (out/'coverage-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
