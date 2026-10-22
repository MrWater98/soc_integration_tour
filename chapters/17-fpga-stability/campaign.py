#!/usr/bin/env python3
"""Run separate continuous and warm-reset campaigns from an explicit JSON plan."""
import argparse,json,subprocess,sys
from pathlib import Path
CHAPTER=Path(__file__).resolve().parent
ROOT=CHAPTER.parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=CHAPTER/'campaign.json');p.add_argument('--serial',required=True);p.add_argument('--output',type=Path,default=ROOT/'results/17-campaign');args=p.parse_args()
 cfg=json.loads(args.config.read_text());out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 results=[];summary={'status':'RUNNING','cases':results,'cold_boot':'NOT_RUN: physical power cycling required','voltage_range':'NOT_RUN','temperature_range':'NOT_RUN'}
 try:
  for case in cfg['cases']:
   if case['seconds']<5 or case['warm_resets']<0:raise ValueError('invalid campaign case')
   src=ROOT/case['input'];target=out/case['name']
   cmd=[sys.executable,str(CHAPTER/'run.py'),'--input',str(src),'--output',str(target),'--serial',args.serial,'--seconds',str(case['seconds']),'--warm-resets',str(case['warm_resets']),'--load']
   for option in ('ambient_c','supply_v','board_id','measurement_note'):
    if cfg.get(option) is not None:cmd.extend(['--'+option.replace('_','-'),str(cfg[option])])
   subprocess.run(cmd,check=True)
   results.append(json.loads((target/'summary.json').read_text()))
   (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
  summary['status']='PASS: configured digital campaigns; physical range tests pending'
 except Exception as e:summary['status']='FAIL';summary['error']=str(e);raise
 finally:
  (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
  (out/'REPORT.md').write_text('# 17 验收集合\n\n'+summary['status']+'\n\n温度、电压范围和物理冷启动未验证；详见 summary.json。\n')
if __name__=='__main__':main()
