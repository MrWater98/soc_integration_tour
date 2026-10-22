#!/usr/bin/env python3
"""Sweep nextpnr seeds on one frozen Tang netlist; timing failure is measured, not hidden."""
import argparse,concurrent.futures,gzip,hashlib,json,re,shutil,statistics,subprocess,time
from pathlib import Path
CHAPTER=Path(__file__).resolve().parent
ROOT=CHAPTER.parents[1]

def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--netlist',type=Path,default=ROOT/'results/15-tang20k-150mhz/netlist.json')
 p.add_argument('--constraints',type=Path,default=ROOT/'results/14-tang20k-150mhz/constraints/tutorial14.cst')
 p.add_argument('--rtl',type=Path,default=ROOT/'results/15-tang20k-150mhz/rtl')
 p.add_argument('--output',type=Path,default=ROOT/'results/14e')
 p.add_argument('--seeds',default='1,2,3,4,5,6,7,8,9,10,11,12')
 p.add_argument('--target-mhz',type=float,default=150)
 p.add_argument('--jobs',type=int,default=2)
 p.add_argument('--timeout',type=float,default=180)
 p.add_argument('--placer',choices=['heap','sa','static'],default='heap')
 p.add_argument('--router',choices=['default','router1','router2'],default='default')
 p.add_argument('--timingweight',type=int,default=10)
 p.add_argument('--critexp',type=int,default=2)
 p.add_argument('--beta',type=float,default=0.9)
 p.add_argument('--tmg-ripup',action='store_true')
 p.add_argument('--router2-alt-weights',action='store_true')
 p.add_argument('--analyze-existing',action='store_true',help='reclassify saved logs/reports without running nextpnr again')
 p.add_argument('--replay',action='store_true',help='use frozen inputs already stored in output/input')
 args=p.parse_args();seeds=[int(s) for s in args.seeds.split(',')]
 if not seeds or len(set(seeds))!=len(seeds) or any(s<1 or s>0xffffffff for s in seeds):p.error('distinct positive uint32 seeds required')
 if not 1<=args.jobs<=4 or args.timeout<=0 or args.target_mhz<=0:p.error('jobs 1..4; positive timeout/frequency')
 if args.timingweight<=0 or args.critexp<=0 or not 0<args.beta<=1:p.error('positive timing weight/criticality exponent; beta in (0,1]')
 algorithm_args=['--placer',args.placer,'--router',args.router]
 if args.placer=='heap':algorithm_args+=['--placer-heap-timingweight',str(args.timingweight),'--placer-heap-critexp',str(args.critexp),'--placer-heap-beta',str(args.beta)]
 if args.tmg_ripup:algorithm_args+=['--tmg-ripup']
 if args.router2_alt_weights:algorithm_args+=['--router2-alt-weights']
 out=args.output.resolve();out.mkdir(parents=True,exist_ok=True);prior_summary=json.loads((out/'summary.json').read_text()) if args.analyze_existing and (out/'summary.json').exists() else None;(out/'summary.json').unlink(missing_ok=True)
 inputs=out/'input';inputs.mkdir(exist_ok=True)
 if args.replay:
  raw=gzip.decompress((inputs/'netlist.json.gz').read_bytes());cst=(inputs/'tutorial14.cst').read_bytes()
  frozen=json.loads((inputs/'manifest.json').read_text())
  if sha(raw)!=frozen['netlist_sha256'] or sha(cst)!=frozen['constraints_sha256']:raise RuntimeError('Frozen input hash mismatch')
 else:
  raw=args.netlist.read_bytes();cst=args.constraints.read_bytes()
  (inputs/'netlist.json.gz').write_bytes(gzip.compress(raw,mtime=0));(inputs/'tutorial14.cst').write_bytes(cst)
  rtl=out/'rtl';rtl.mkdir(exist_ok=True)
  for f in args.rtl.iterdir():
   if f.suffix in ('.v','.sv','.vh','.init') or f.name in ('sources.json','YOSYS_COPYING'):shutil.copyfile(f,rtl/f.name)
  frozen={'netlist_sha256':sha(raw),'constraints_sha256':sha(cst),'netlist_origin':str(args.netlist.resolve()),'constraints_origin':str(args.constraints.resolve()),'rtl_origin':str(args.rtl.resolve()),'hardware_configuration':'chapter 14 input configuration; fixed for all seeds','rtl_files':{f.name:sha(f.read_bytes()) for f in sorted(rtl.iterdir()) if f.suffix in ('.v','.sv','.vh','.init')}}
  platform_manifest=args.constraints.resolve().parent.parent/'manifest.json'
  if platform_manifest.exists():
   platform_data=platform_manifest.read_bytes();(inputs/'platform-manifest.json').write_bytes(platform_data);frozen['platform_manifest_sha256']=sha(platform_data)
  write(inputs/'manifest.json',frozen)
 (inputs/'netlist.json').write_bytes(raw)
 binary=shutil.which('nextpnr-himbaechel') or str(ROOT/'external/fpga-tools/oss-cad-suite/bin/nextpnr-himbaechel')
 version=subprocess.run([binary,'--version'],capture_output=True,text=True,check=True)
 configuration={'target_mhz':args.target_mhz,'seeds':seeds,'jobs':args.jobs,'timeout_seconds':args.timeout,'tool_version':(version.stdout+version.stderr).strip(),'device':'GW2A-LV18PG256C8/I7','family':'GW2A-18C','netlist_sha256':sha(raw),'constraints_sha256':sha(cst),'timing_allow_fail':False,'hardware':'NOT_RUN','only_varied_parameter':'seed','algorithm_args':algorithm_args,'placer':args.placer,'router':args.router}
 write(out/'config.json',configuration);rows=[];commands=[];campaign_started=time.monotonic()
 def case(seed):
  directory=out/f'seed-{seed:03d}';directory.mkdir(exist_ok=True)
  if not args.analyze_existing:
   for f in ('pnr-report.json','routed.json'): (directory/f).unlink(missing_ok=True)
  cmd=[binary,'--json',str(inputs/'netlist.json'),'--write',str(directory/'routed.json'),'--report',str(directory/'pnr-report.json'),'--top','tutorial14','--device',configuration['device'],'--vopt','family='+configuration['family'],'--vopt','cst='+str(inputs/'tutorial14.cst'),'--freq',str(args.target_mhz),'--seed',str(seed)]+algorithm_args
  if args.analyze_existing:
   prior=json.loads((directory/'summary.json').read_text());cmd=json.loads((directory/'command.json').read_text())
   returncode=prior['exit_code'];timed_out=prior['status']=='TIMEOUT';elapsed=prior['elapsed_seconds']
  else:
   write(directory/'command.json',cmd);start=time.monotonic();timed_out=False
   with (directory/'nextpnr.log').open('w') as log:
    try:result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=args.timeout);returncode=result.returncode
    except subprocess.TimeoutExpired:timed_out=True;returncode=None
   elapsed=time.monotonic()-start
  row={'seed':seed,'elapsed_seconds':elapsed,'exit_code':returncode,'status':'TIMEOUT' if timed_out else 'TOOL_ERROR'}
  log=(directory/'nextpnr.log').read_text();report_path=directory/'pnr-report.json'
  routing_complete='Routing complete.' in log or ('Router2 time' in log and re.search(r'iter=\d+[^\n]*overused=0 overuse=0(?: tmgfail=\d+)? archfail=0',log) is not None)
  if report_path.exists() and (directory/'routed.json').exists() and routing_complete and not timed_out:
   report=json.loads(report_path.read_text());clocks=report.get('fmax',{})
   unexpected=[line for line in log.splitlines() if line.startswith('ERROR:') and 'Max frequency for clock' not in line]
   if 'VexRiscv.clk' in clocks and not unexpected and returncode in (0,1):
    passes=all(c['constraint']>=args.target_mhz and c['achieved']>=c['constraint'] for c in clocks.values())
    row.update(status='PASS' if passes and returncode==0 else 'TIMING_FAIL',system_fmax_mhz=clocks['VexRiscv.clk']['achieved'],limiting_fmax_mhz=min(c['achieved'] for c in clocks.values()),clocks=clocks,routed_sha256=sha((directory/'routed.json').read_bytes()))
    candidates=[x for x in report['critical_paths'] if 'VexRiscv.clk' in x.get('from','') and 'VexRiscv.clk' in x.get('to','')]
    if candidates:
     path=max(candidates,key=lambda x:sum(e['delay'] for e in x['path']))['path'];delays={}
     for entry in path:delays[entry['type']]=delays.get(entry['type'],0)+entry['delay']
     row['critical_path']={'start':path[0]['from'],'end':path[-1]['to'],'delay_ns_by_type':delays,'total_delay_ns':sum(delays.values())}
  if row['status']=='TOOL_ERROR':
   if returncode is not None and returncode<0:row['terminated_by_signal']=-returncode
   row['error_details']=[line for line in log.splitlines() if line.startswith('ERROR:') or 'Assertion failure:' in line or 'terminate called' in line][-6:]
  write(directory/'summary.json',row)
  print(f"seed={seed} status={row['status']} fmax={row.get('system_fmax_mhz','N/A')} MHz elapsed={row['elapsed_seconds']:.2f}s",flush=True)
  return row,cmd
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
  futures=[pool.submit(case,s) for s in seeds]
  for future in concurrent.futures.as_completed(futures):
   row,cmd=future.result();rows.append(row);commands.append(cmd);write(out/'progress.json',sorted(rows,key=lambda r:r['seed']))
 rows.sort(key=lambda r:r['seed']);valid=[r for r in rows if r['status'] in ('PASS','TIMING_FAIL')]
 if not valid:
  write(out/'summary.json',{'status':'NO_VALID_TIMING_RESULTS','configuration':configuration,'results':rows,'valid_runs':0,'target_passes':0,'best':None,'worst':None,'median_limiting_fmax_mhz':None,'wall_seconds':time.monotonic()-campaign_started,'bitstream':'NOT_PACKED','hardware':'NOT_RUN'})
  write(out/'commands.json',commands)
  (out/'REPORT.md').write_text('# 14E：没有完整时序结果\n\n请查看各 seed 的 summary.json 和 nextpnr.log；工具错误/超时不参与 Fmax 排名。\n')
  print('NO_VALID_TIMING_RESULTS',flush=True);return
 best=max(valid,key=lambda r:r['limiting_fmax_mhz']);worst=min(valid,key=lambda r:r['limiting_fmax_mhz'])
 bestdir=out/f"seed-{best['seed']:03d}";bestout=out/'best';bestout.mkdir(exist_ok=True)
 (bestout/'routed.json.gz').write_bytes(gzip.compress((bestdir/'routed.json').read_bytes(),mtime=0))
 shutil.copyfile(bestdir/'pnr-report.json',bestout/'pnr-report.json');write(bestout/'summary.json',best)
 summary={'status':'COMPLETE: finite seed exploration; physical maximum NOT_MEASURED','configuration':configuration,'results':rows,'best':best,'worst':worst,'median_limiting_fmax_mhz':statistics.median(r['limiting_fmax_mhz'] for r in valid),'valid_runs':len(valid),'target_passes':sum(r['status']=='PASS' for r in rows),'wall_seconds':time.monotonic()-campaign_started,'bitstream':'NOT_PACKED','hardware':'NOT_RUN'}
 if prior_summary:
  summary['analysis_wall_seconds']=summary['wall_seconds'];summary['wall_seconds']=prior_summary['wall_seconds']
 write(out/'summary.json',summary);write(out/'commands.json',commands)
 text='# 14E：固定网表的 seed 实验\n\n只改变 seed；目标、器件、网表和 CST 哈希固定。不使用 timing-allow-fail。\n\n| seed | 状态 | 系统时钟域 Fmax MHz | 限制频率 MHz | 耗时秒 |\n| --- | --- | ---: | ---: | ---: |\n'
 for row in rows:text+=f"| {row['seed']} | {row['status']} | {row.get('system_fmax_mhz',0):.2f} | {row.get('limiting_fmax_mhz',0):.2f} | {row['elapsed_seconds']:.2f} |\n"
 text+=f"\n最佳 seed={best['seed']}，本组最低时钟 Fmax 估计 {best['limiting_fmax_mhz']:.2f} MHz。{args.target_mhz:g} MHz 目标通过 {summary['target_passes']}/{len(rows)}。不是板上最高频率，也不是所有 seed 的全局最优。\n"
 (out/'REPORT.md').write_text(text)
 print('BEST',best['seed'],best['limiting_fmax_mhz'],'MHz',flush=True)
if __name__=='__main__':main()
