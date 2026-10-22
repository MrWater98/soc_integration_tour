#!/usr/bin/env python3
"""Execute real CPU firmware/UART/button/reset RTL with a ideal 27MHz PLL substitute."""
import argparse,json,subprocess,shutil
from pathlib import Path
CHAPTER=Path(__file__).resolve().parent
ROOT=CHAPTER.parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--cxx',default=shutil.which('g++-11') or shutil.which('g++'),help='C++20 compiler for Verilator timing simulation')
p.add_argument('--input',type=Path,default=ROOT/'results/14-tang20k')
a=p.parse_args();result=a.input.resolve()
manifest=json.loads((result/'manifest.json').read_text())
if manifest['config']['sys_clk_hz']!=27000000 or manifest['config']['baud']!=115200:raise ValueError('this testbench is for 27MHz/115200 configuration')
rtl=result/'rtl';obj=result/'digital-obj';binary=obj/'Vtb'
cmd=['verilator','--binary','--timing','--top-module','tb','-Wno-fatal','-CFLAGS','-std=c++20','-MAKEFLAGS',f'CXX={a.cxx}','-j','2','--Mdir',str(obj),
     'VexRiscv.v','tutorial14.v','gowin_sim_primitives.v','tang_tb.sv']
with (result/'digital-compile.log').open('w') as stream:
    compiled=subprocess.run(cmd,cwd=rtl,stdout=stream,stderr=subprocess.STDOUT)
if compiled.returncode:raise RuntimeError(f'compile failed; inspect {result/"digital-compile.log"}')
with (result/'digital-sim.log').open('w') as stream:
    run=subprocess.run([str(binary)],cwd=rtl,stdout=stream,stderr=subprocess.STDOUT,timeout=60)
text=(result/'digital-sim.log').read_text()
if run.returncode or 'PASS TANG_DIGITAL_BOOT_BUTTON_RESET' not in text:raise RuntimeError(text)
(result/'digital-summary.json').write_text(json.dumps(dict(status='PASS',checks=['CPU boot and UART','button 0->1->0 and LED','reset and second HELLO'],pll='ideal reference-clock substitute; analog behavior NOT_TESTED'),indent=2)+'\n')
report=result/'REPORT.md'
base=report.read_text().split('\n## 数字集成仿真')[0]
report.write_text(base+'\n## 数字集成仿真\n\nPASS：真实 VexRiscv 执行固件，经真实 UART TX 引脚解码；按钮值 0→1→0、LED5 对应变化、复位后再次 HELLO。PLL 使用理想 27 MHz 仿真替代模型，不验证模拟锁定行为。\n')
print(text)
