#!/usr/bin/env python3
"""Drive output pads and capture input pads through a real teaching TAP."""
import argparse,json
from pathlib import Path
from visualize import render
from pin_driver import Pins
CHAPTER=Path(__file__).resolve().parent
ROOT=CHAPTER.parent.parent if CHAPTER.parent.name=='chapters' else CHAPTER

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'results/13b');args=p.parse_args()
 args.output.mkdir(parents=True,exist_ok=True)
 for stale in ('summary.json','REPORT.md','pins.html'):(args.output/stale).unlink(missing_ok=True)
 pins=Pins(CHAPTER,args.output); rows=[]
 try:
  pins.reset();pins.scan(4,4,ir=True)
  sample=pins.scan(0,8)
  assert sample==0xaa and pins.last[4]==0xa
  rows.append(dict(case='sample-functional',observed=sample,status='PASS'))
  # SAMPLE loads the output update latch while leaving functional outputs connected.
  pins.scan(0x10,8);assert pins.last[4]==0xa
  pins.scan(5,4,ir=True);assert pins.last[4]==1
  rows.append(dict(case='preload-then-extest',observed=pins.last[4],status='PASS'))
  for mode,label in ((0,'healthy'),(1,'stuck-low-bit1'),(2,'wired-or-short-bits01')):
   for pattern in (1,2,4,8,15,0):
    old=pins.last[4];pins.scan(pattern<<4,8,mode=mode,hold_output=old)
    assert pins.last[4]==pattern
    read=pins.scan(pattern<<4,8,mode=mode,hold_output=pattern)&15
    expected=pattern if mode==0 else (pattern&13 if mode==1 else (pattern&12)|(3 if pattern&3 else 0))
    assert read==expected
    rows.append(dict(case=label,drive=pattern,captured=read,normal_expected=pattern,mismatch_mask=read^pattern,status='PASS'))
  assert any(x.get('mismatch_mask',0) for x in rows if x['case']=='stuck-low-bit1')
  assert any(x.get('mismatch_mask',0) for x in rows if x['case']=='wired-or-short-bits01')
  pins.scan(4,4,ir=True);assert pins.last[4]==0xa
  rows.append(dict(case='release-functional',observed=pins.last[4],status='PASS'))
 finally:pins.close()
 summary={'status':'PASS','cases':rows,'pins':4,'boundary_bits':8,'fault_model':'digital stuck-low / wired-OR; not analog electrical simulation'}
 (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 (args.output/'REPORT.md').write_text('# 13B 边界扫描实验\n\nPASS：SAMPLE、预装载、EXTEST、逐位激励、故障读回与释放。\n\n|场景|输出|采样|与正常值异或|\n|---|---|---|---|\n'+''.join(f"|{x['case']}|{x.get('drive','—')}|{x.get('captured',x.get('observed'))}|{x.get('mismatch_mask','—')}|\n" for x in rows))
 render(args.output/'pins.csv',args.output/'pins.html')
 print(f"PASS 13B: {len(rows)} checks; {args.output}")
if __name__=='__main__':main()
