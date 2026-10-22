#!/usr/bin/env python3
"""An independent JTAG tester drives a real SV TAP and checks serial results."""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
from visualize import render
import re
import shutil
import subprocess

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent if CHAPTER.parent.name == 'chapters' else CHAPTER
NAMES = ('RESET','IDLE','SELECT_DR','CAPTURE_DR','SHIFT_DR','EXIT1_DR','PAUSE_DR',
         'EXIT2_DR','UPDATE_DR','SELECT_IR','CAPTURE_IR','SHIFT_IR','EXIT1_IR',
         'PAUSE_IR','EXIT2_IR','UPDATE_IR')
# Explicit tester specification: next-state for TMS=0 and TMS=1.
NEXT = ((1,0),(1,2),(3,9),(4,5),(4,5),(6,8),(6,7),(4,8),
        (1,2),(10,0),(11,12),(11,12),(13,15),(13,14),(11,15),(1,2))


class Tester:
    def __init__(self):
        self.state = 0
        self.vectors = []
        self.checks = []

    def tick(self, tms, tdi=0):
        index = len(self.vectors)
        after = NEXT[self.state][tms]
        self.vectors.append((tms,tdi,self.state,after))
        self.state = after
        return index

    def reset(self):
        for _ in range(5): self.tick(1)
        self.tick(0)

    def enter(self, ir=False):
        assert self.state == 1
        self.tick(1)
        if ir: self.tick(1)
        self.tick(0); self.tick(0)

    def finish(self):
        self.tick(1); self.tick(0)
        assert self.state == 1

    def scan(self, value, bits, *, ir=False, expected=None, expected_bits=None, diagnostic=None):
        self.enter(ir)
        slots = [self.tick(int(i == bits-1), (value >> i) & 1) for i in range(bits)]
        self.finish()
        self.checks.append(dict(slots=slots, expected=expected, bits=expected_bits or bits,
                                diagnostic=diagnostic, kind='IR' if ir else 'DR'))
        return slots


def cases(ir_len, idcode):
    built = []
    def new(name):
        t = Tester(); t.reset(); built.append((name,t)); return t
    t=new('idcode');t.scan(0,32,expected=idcode)
    t=new('capture-ir');t.scan(2,ir_len,ir=True,expected=1);t.scan(0,32,expected=idcode)
    t=new('user-register');t.scan(3,ir_len,ir=True,expected=1)
    t.scan(0x2468ace1,32,expected=0xcafef00d);t.scan(0,32,expected=0x2468ace1)
    t=new('bypass');t.scan((1<<ir_len)-1,ir_len,ir=True,expected=1)
    pattern=0b101011001110;t.scan(pattern,12,expected=(pattern<<1)&((1<<12)-1))
    t=new('wrong-ir');t.scan(4,ir_len,ir=True,expected=1)
    t.scan(0,32,expected=idcode,diagnostic='WRONG_IR_READBACK')
    t=new('short-scan');t.scan(0,31,expected=idcode,expected_bits=32,diagnostic='SHORT_SCAN')
    t=new('wrong-bit-order');t.scan(3,ir_len,ir=True,expected=1)
    t.scan(0,32,expected=0xcafef00d,diagnostic='WRONG_BIT_ORDER')
    t=new('reset-during-scan');t.scan(3,ir_len,ir=True,expected=1);t.enter()
    partial=[t.tick(0,1) for _ in range(8)]
    t.checks.append(dict(slots=partial,expected=0xcafef00d,bits=32,diagnostic='RESET_INTERRUPTED_SCAN',kind='DR'))
    t.reset();t.scan(0,32,expected=idcode)
    t=new('pause-resume');t.enter();slots=[]
    for i in range(8):slots.append(t.tick(int(i==7)))
    t.tick(0)
    for _ in range(3):t.tick(0)
    t.tick(1);t.tick(0)
    for i in range(24):slots.append(t.tick(int(i==23)))
    t.finish();t.checks.append(dict(slots=slots,expected=idcode,bits=32,diagnostic=None,kind='DR'))
    t=new('all-state-edges')
    for target in range(16):
        for bit in (0,1):
            # Reach each state independently, then exercise each outgoing edge.
            t.reset(); queue=deque([(t.state,[])])
            seen={t.state}
            while queue:
                current,path=queue.popleft()
                if current==target:break
                for tm in (0,1):
                    after=NEXT[current][tm]
                    if after not in seen:seen.add(after);queue.append((after,path+[tm]))
            for tm in path:t.tick(tm)
            t.tick(bit)
    return built


def main():
    parser=argparse.ArgumentParser(description='13A 最小 TAP 仿真与可解释故障')
    parser.add_argument('--output',type=Path,default=ROOT/'results/13a')
    parser.add_argument('--ir-length',type=int,default=4)
    parser.add_argument('--idcode',type=lambda text:int(text,0),default=0x12345679)
    args=parser.parse_args()
    if not 4<=args.ir_length<=16 or not 0<=args.idcode<2**32 or not args.idcode&1:
        parser.error('IR length 4..16; example IDCODE is a 32-bit odd value')
    for tool in ('iverilog','vvp'):
        if not shutil.which(tool):raise RuntimeError(f'missing {tool}; install iverilog')
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    (out/'summary.json').unlink(missing_ok=True)
    rtl=out/'rtl';rtl.mkdir(exist_ok=True)
    sources=[]
    for name in ('tap.sv','tb.sv'):
        shutil.copy2(CHAPTER/name,rtl/name)
        sources.append(dict(file=name,sha256=hashlib.sha256((rtl/name).read_bytes()).hexdigest()))
    (rtl/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
    (rtl/'files.f').write_text('tap.sv\ntb.sv\n')
    binary=out/'tap.vvp'
    command=['iverilog','-g2012','-s','tb',f'-DIR_LENGTH={args.ir_length}',
             f"-DIDCODE_VALUE=32'h{args.idcode:08x}",'-o',str(binary),str(rtl/'tap.sv'),str(rtl/'tb.sv')]
    compiled=subprocess.run(command,capture_output=True,text=True,timeout=30)
    (out/'compile.log').write_text(compiled.stdout+compiled.stderr)
    compiled.check_returncode()
    summary=[];edges=set();case_dir=out/'cases';case_dir.mkdir(exist_ok=True)
    for name,tester in cases(args.ir_length,args.idcode):
        vectors=case_dir/f'{name}.vectors'
        vectors.write_text(''.join(' '.join(map(str,row))+'\n' for row in tester.vectors))
        run=subprocess.run(['vvp',str(binary),f'+vectors={vectors}',f'+wave={case_dir/name}.vcd'],
                           capture_output=True,text=True,timeout=10)
        log=run.stdout+run.stderr;(case_dir/f'{name}.log').write_text(log);run.check_returncode()
        rows=[tuple(map(int,match)) for match in re.findall(r'TAP_CYCLE index=(\d+) pre=(\d+) tms=(\d+) tdi=(\d+) tdo=(\d+) post=(\d+)',log)]
        if len(rows)!=len(tester.vectors):raise AssertionError('incomplete cycle trace')
        csv=['cycle,pre,tms,tdi,tdo,post']
        for index,pre,tms,tdi,tdo,post in rows:
            edges.add((pre,tms));csv.append(f'{index},{NAMES[pre]},{tms},{tdi},{tdo},{NAMES[post]}')
        (case_dir/f'{name}.csv').write_text('\n'.join(csv)+'\n')
        diagnoses=[];values=[]
        for check in tester.checks:
            bits=[rows[index][4] for index in check['slots']]
            value=sum(bit<<i for i,bit in enumerate(bits))
            interpreted=value
            if check['diagnostic']=='WRONG_BIT_ORDER':interpreted=int(''.join(map(str,bits)),2)
            mismatch=len(bits)!=check['bits'] or interpreted!=check['expected']
            if check['diagnostic']:
                if not mismatch:raise AssertionError(f'{name}: injected error escaped checker')
                diagnoses.append(check['diagnostic'])
            elif mismatch:raise AssertionError(f'{name}: read 0x{value:x}, expected 0x{check["expected"]:x}')
            values.append(dict(kind=check['kind'],bits=len(bits),value=f'0x{value:x}',interpreted=f'0x{interpreted:x}',expected=f'0x{check["expected"]:x}'))
        result=dict(case=name,status='PASS',cycles=len(rows),diagnoses=diagnoses,scans=values)
        summary.append(result);print(f'PASS 13A-{name}: '+(','.join(diagnoses) or 'state and serial evidence'),flush=True)
    if len(edges)!=32:raise AssertionError(f'state edge coverage {len(edges)}/32')
    report=dict(status='PASS',ir_length=args.ir_length,idcode=f'0x{args.idcode:08x}',state_edges=f'{len(edges)}/32',cases=summary,
                tools=dict(iverilog=subprocess.run(['iverilog','-V'],capture_output=True,text=True).stdout.splitlines()[0]),sources=sources)
    (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'REPORT.md').write_text('# 13A TAP 验证\n\n'+f'PASS：{len(summary)} 个场景；状态转移 {len(edges)}/32；IR {args.ir_length} 位；示例 IDCODE 0x{args.idcode:08x}。\n\n'+
        '\n'.join((f'- {row["case"]}: PASS '+','.join(row['diagnoses'])).rstrip() for row in summary)+'\n')
    render(case_dir/'idcode.csv',out/'pins.html',per_cycle=True)
    print(f'PASS 13A: {len(summary)} cases, {len(edges)}/32 state edges; {out}')


if __name__=='__main__':main()
