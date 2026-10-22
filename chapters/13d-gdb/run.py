#!/usr/bin/env python3
"""Learn actual GDB on a local process before adding remote CPU hardware."""
import argparse,json,re,shutil,subprocess
from pathlib import Path
CHAPTER=Path(__file__).resolve().parent
ROOT=CHAPTER.parent.parent if CHAPTER.parent.name=='chapters' else CHAPTER

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'results/13d');args=p.parse_args()
 out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 for stale in ('summary.json','REPORT.md'):(out/stale).unlink(missing_ok=True)
 for name in ('fact.c','session.gdb'):shutil.copyfile(CHAPTER/name,out/name)
 subprocess.run(['gcc','-g','-O0','-fno-omit-frame-pointer','-fno-optimize-sibling-calls','fact.c','-o','fact'],cwd=out,check=True,timeout=30)
 result=subprocess.run(['gdb','-q','-nx','-batch','-x','session.gdb','./fact'],cwd=out,capture_output=True,text=True,timeout=30)
 log=result.stdout+result.stderr;(out/'gdb.log').write_text(log);result.check_returncode()
 entered=list(map(int,re.findall(r'FRAME_N=(\d+)',log)));returned=list(map(int,re.findall(r'BACK_IN_N=(\d+)',log)))
 stack=list(map(lambda value:int(value,16),re.findall(r'SP_VALUE=(0x[0-9a-fA-F]+)',log)))
 assert entered==[3,2,1] and returned==[2,3]
 assert len(stack)==5 and len(set(stack[:3]))==3 and stack[3:]==[stack[1],stack[0]]
 assert 'fact(3)=6' in log and 'exited normally' in log
 assert re.search(r'#0\s+fact',log) and re.search(r'#3\s+.*main',log)
 summary={'status':'PASS','backend':'native host process via OS; no JTAG or OpenOCD','entered':entered,'returned':returned,'result':6,'stack_pointers':[hex(value) for value in stack],'sp_offsets_from_fact3':[value-stack[0] for value in stack]}
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 (out/'REPORT.md').write_text('# 13D GDB 入门\n\nPASS：断点进入 fact(3)、fact(2)、fact(1)，观察调用栈，finish 返回 fact(2)、fact(3)，结果为 6。\n\n'+f'目标架构：{subprocess.check_output(["gcc","-dumpmachine"],text=True).strip()}。这是宿主进程调试；未连接 SoC。\n')
 with (out/'REPORT.md').open('a') as report:
  report.write('\n|停下位置|SP 相对 fact(3) 的变化（字节）|\n|---|---|\n'+''.join(f'|{label}|{value-stack[0]}|\n' for label,value in zip(('fact(3)','fact(2)','fact(1)','返回 fact(2)','返回 fact(3)'),stack)))
 print('PASS 13D: break, step, PC/SP, backtrace, finish, continue')
if __name__=='__main__':main()
