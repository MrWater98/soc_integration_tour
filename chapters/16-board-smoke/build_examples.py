#!/usr/bin/env python3
"""Build small Tang Primer 20K Dock experiments, without accessing USB."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
CHAPTER=Path(__file__).resolve().parent
ROOT=CHAPTER.parent.parent if CHAPTER.parent.name=='chapters' else CHAPTER
DEVICE='GW2A-LV18PG256C8/I7'
FAMILY='GW2A-18C'

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--example',choices=('leds','clock','rgb_led','sound'),default='leds')
 parser.add_argument('--output',type=Path)
 parser.add_argument('--tools',type=Path,default=ROOT/'external/fpga-tools/oss-cad-suite/bin')
 parser.add_argument('--seed',type=int,default=1)
 args=parser.parse_args();name=args.example
 out=(args.output or ROOT/f'results/16-{name}').resolve();out.mkdir(parents=True,exist_ok=True)
 for stale in ('summary.json','REPORT.md',name+'.fs'):(out/stale).unlink(missing_ok=True)
 env=dict(os.environ);env['PATH']=str(args.tools.resolve())+os.pathsep+env['PATH']
 def tool(name):
  found=shutil.which(name,path=env['PATH'])
  if not found:raise RuntimeError('Missing '+name+'; activate or specify OSS CAD Suite')
  return found
 rtl=out/'rtl';rtl.mkdir(exist_ok=True);constraints=out/'constraints';constraints.mkdir(exist_ok=True)
 design_files=[name+'.v']+(['sound_rom.v'] if name=='sound' else [])
 for filename in design_files:shutil.copyfile(CHAPTER/'examples'/name/filename,rtl/filename)
 if name=='sound':
  shutil.copyfile(CHAPTER/'examples/LICENSES/CC0-1.0.txt',rtl/'LICENSE-CC0-1.0.txt')
  shutil.copyfile(CHAPTER/'examples/sound/AUDIO-LICENSE.txt',rtl/'AUDIO-LICENSE.txt')
 shutil.copyfile(CHAPTER/'examples'/name/'constraints.cst',constraints/(name+'.cst'))
 shutil.copyfile(CHAPTER/'examples/LICENSES/WTFPL.txt',rtl/'LICENSE-WTFPL.txt')
 (rtl/'files.f').write_text(''.join(filename+'\n' for filename in design_files))
 (rtl/'sources.json').write_text(json.dumps([{'file':filename,'sha256':hashlib.sha256((rtl/filename).read_bytes()).hexdigest(),'upstream':'twied/TangPrimer-20K-example@7f26660abc25e1b79f6709bd00ca9cead8706494'} for filename in design_files],indent=2)+'\n')
 verilog_inputs=' '.join('rtl/'+filename for filename in design_files)
 commands=[
 [tool('yosys'),'-p',f'read_verilog {verilog_inputs}; synth_gowin -top {name} -family gw2a -json netlist.json; check -assert'],
 [tool('nextpnr-himbaechel'),'--json','netlist.json','--write','routed.json','--report','pnr-report.json','--device',DEVICE,'--vopt','family='+FAMILY,'--vopt',f'cst=constraints/{name}.cst','--freq','27','--seed',str(args.seed)],
 [tool('gowin_pack'),'-d',FAMILY,'--ready_as_gpio','--done_as_gpio','-o',name+'.fs','routed.json']]
 (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 for command,label in zip(commands,('yosys','nextpnr','pack')):
  with (out/(label+'.log')).open('w') as log:
   result=subprocess.run(command,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
  if result.returncode:raise RuntimeError(label+' failed; inspect '+str(out/(label+'.log')))
 report=json.loads((out/'pnr-report.json').read_text())
 if name!='leds':
  assert report.get('fmax'),'Missing clock timing report'
  for clk,value in report['fmax'].items():
   assert value['constraint']>=27 and value['achieved']>=value['constraint'],f'Timing target failed: {clk}'
 data=(out/(name+'.fs')).read_bytes();assert data
 summary={'build':'PASS','onboard':'NOT_RUN: requires real detection/download/observation','example':name,'device':DEVICE,'family':FAMILY,'bitstream_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'clock_target_mhz':27 if name!='leds' else None,'resources':report['utilization'],'seed':args.seed}
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 (out/'REPORT.md').write_text(f'# Tang Primer 20K {name}\n\nPASS：Yosys 综合、nextpnr 布局布线、Apicula bitstream。\n\n器件 `{DEVICE}`，数据库 `{FAMILY}`。'+ ('27 MHz 时钟目标通过。' if name!='leds' else '纯组合固定输出，没有工作时钟。')+f'\n\nbitstream：`{name}.fs`，SHA256 `{summary["sha256"]}`。\n\n上板：NOT_RUN，等待 USB 转交、识别与实际灯光观察。\n')
 print('PASS build',name,out/(name+'.fs'))
if __name__=='__main__':main()
