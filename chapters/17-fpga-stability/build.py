#!/usr/bin/env python3
"""Self-contained Tang stability SoC, firmware, complete RTL and open FPGA build."""
import argparse,hashlib,json,logging,os,shutil,subprocess,sys
from contextlib import redirect_stdout,redirect_stderr
from dataclasses import dataclass
from pathlib import Path
from config import Config as BoardConfig
from firmware_builder import firmware
CHAPTER=Path(__file__).resolve().parent
ROOT=CHAPTER.parent.parent if CHAPTER.parent.name=='chapters' else CHAPTER
sys.path.insert(0,str(ROOT))
try:from tutorial_paths import add_litex_to_path
except ModuleNotFoundError:
 def add_litex_to_path(root):
  if os.environ.get('LITEX_ROOT'):sys.path.insert(0,os.environ['LITEX_ROOT'])
@dataclass(frozen=True)
class Config(BoardConfig):
 stress_words:int=512
 seed:int=1
 inject_fault:bool=False

def generate(out,cfg,words,rtl=False):
 from soc import BoardSoC
 from litex.soc.integration.builder import Builder
 with (out/('generate.log' if rtl else 'elaborate.log')).open('w') as stream:
  with redirect_stdout(stream),redirect_stderr(stream):
   logging.basicConfig(level=logging.INFO,stream=stream,force=True)
   soc=BoardSoC(cfg,words);builder=Builder(soc,output_dir=str(out/'builder'),compile_software=False,compile_gateware=False)
   if rtl:builder.build(build_name='tutorial17',run=False)
   else:soc.finalize();builder._generate_includes(with_bios=False);builder._generate_csr_map()
 logging.basicConfig(level=logging.INFO,stream=sys.__stdout__,force=True)
 return soc

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'results/17');p.add_argument('--sys-clk-hz',type=int,default=54000000);p.add_argument('--stress-words',type=int,default=512);p.add_argument('--seed',type=int,default=1);p.add_argument('--inject-fault',action='store_true');p.add_argument('--build',action='store_true');args=p.parse_args()
 cfg=Config(sys_clk_hz=args.sys_clk_hz,stress_words=args.stress_words,seed=args.seed,inject_fault=args.inject_fault).validate()
 if not 16<=cfg.stress_words<=2048 or not 1<=cfg.seed<2**32:p.error('stress words 16..2048; nonzero uint32 seed')
 add_litex_to_path(ROOT);out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 generate(out,cfg,[0x0000006f]);words=firmware(out,cfg,source=CHAPTER/'main.c');soc=generate(out,cfg,words,True)
 gate=out/'builder/gateware';rtl=out/'rtl';rtl.mkdir(exist_ok=True);records=[]
 for path in [Path(row[0]) for row in soc.platform.sources]+list(gate.glob('*.init'))+[CHAPTER/'gowin_primitives.v']:
  if not path.is_absolute():path=gate/path
  if path.suffix not in ('.v','.sv','.vh','.init'):continue
  target=rtl/path.name;target.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()).rstrip()+'\n')
  records.append({'file':path.name,'role':'primitive_library' if path.name=='gowin_primitives.v' else 'design','snapshot_sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
 (rtl/'sources.json').write_text(json.dumps(records,indent=2)+'\n');(rtl/'files.f').write_text(''.join(x['file']+'\n' for x in records if x['file'].endswith(('.v','.sv'))))
 subprocess.run(['iverilog','-g2012','-s','tutorial17','-o',str(out/'elab.vvp'),'-f','files.f'],cwd=rtl,check=True,timeout=30)
 constraints=out/'constraints';constraints.mkdir(exist_ok=True)
 for suffix in ('cst','sdc'):
  if (gate/f'tutorial17.{suffix}').exists():shutil.copyfile(gate/f'tutorial17.{suffix}',constraints/f'tutorial14.{suffix}')
 params=soc.crg.pll.compute_config();assert abs(cfg.reference_clk_hz*params['fdiv']/params['idiv']-cfg.sys_clk_hz)<1
 manifest={'device':'GW2A-LV18PG256C8/I7','family':'GW2A-18C','config':cfg.values,'pll':{k:v for k,v in params.items() if isinstance(v,(str,int,float,bool))},'sources':records}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (out/'REPORT.md').write_text('# 17 稳定性 SoC 构建\n\nPASS：本章独立 CPU/ROM/RAM/UART/Timer IRQ/GPIO/复位 RTL 与固件生成，完整 RTL 展开。\n\n实物压力测试尚未运行。\n')
 if args.build:
  env=dict(os.environ);env['PATH']=str(ROOT/'external/fpga-tools/oss-cad-suite/bin')+os.pathsep+env['PATH']
  subprocess.run([sys.executable,str(CHAPTER/'synthesize.py'),'--family','gw2a','--top','tutorial17','--input',str(rtl),'--output',str(out/'synthesis')],env=env,check=True)
  subprocess.run([sys.executable,str(CHAPTER/'route.py'),'--synthesis',str(out/'synthesis'),'--platform',str(out),'--output',str(out/'build')],env=env,check=True)
 print('PASS 17 build',out)
if __name__=='__main__':main()
