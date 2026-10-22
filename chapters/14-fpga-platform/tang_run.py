#!/usr/bin/env python3
"""Generate the purchased Tang Primer 20K Dock target without any board attached."""
import argparse
import csv
import hashlib
import json
import logging
from pathlib import Path
import re
import shutil
import subprocess
import sys
from contextlib import redirect_stdout,redirect_stderr
from build_utils import CHAPTER,ROOT,add_litex_to_path,write,sha
from firmware import firmware
from checks import check_logic
from tang_config import Config

# Independent pin facts, compared against the native platform's generated CST.
PINS={'clk27':('H11','LVCMOS33'),'serial_rx':('T13','LVCMOS33'),
      'serial_tx':('M11','LVCMOS33'),'btn_n0':('T10','LVCMOS33'),
      'btn_n1':('T3','LVCMOS15'),'led4':('A13','LVCMOS33'),'led5':('C13','LVCMOS33')}

def generate(result,cfg,words,rtl=False):
    from litex.soc.integration.builder import Builder
    from tang_soc import BoardSoC
    with (result/('generate.log' if rtl else 'elaborate.log')).open('w') as stream:
        with redirect_stdout(stream),redirect_stderr(stream):
            logging.basicConfig(level=logging.INFO,stream=stream,force=True)
            soc=BoardSoC(cfg,words)
            builder=Builder(soc,output_dir=str(result/'builder'),compile_software=False,compile_gateware=False)
            if rtl:builder.build(build_name='tutorial14',run=False)
            else:soc.finalize();builder._generate_includes(with_bios=False);builder._generate_csr_map()
    logging.basicConfig(level=logging.INFO,stream=sys.__stdout__,force=True)
    return soc

def audit_cst(text):
    locs=dict(re.findall(r'IO_LOC\s+"([^"\n]+)"\s+(\w+)\s*;',text))
    standards=dict(re.findall(r'IO_PORT\s+"([^"\n]+)"\s+IO_TYPE=(\w+)',text))
    if set(locs)!=set(PINS):raise AssertionError(f'pin set differs: {locs}')
    if len(set(locs.values()))!=len(locs):raise AssertionError('duplicate package pin')
    for port,(pin,standard) in PINS.items():
        if locs[port]!=pin or standards.get(port)!=standard:raise AssertionError(f'{port}: expected {pin}/{standard}, actual {locs[port]}/{standards.get(port)}')
    return locs

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'results/14-tang20k')
    for name in ('sys_clk_hz','baud','blink_hz','rom_size','sram_size','main_ram_size','stack_size','por_cycles'):
        parser.add_argument('--'+name.replace('_','-'),type=lambda text:int(text,0))
    args=parser.parse_args();cfg=Config(**{k:v for k,v in vars(args).items() if k!='output' and v is not None}).validate()
    add_litex_to_path(ROOT)
    result=args.output.resolve();result.mkdir(parents=True,exist_ok=True);(result/'summary.json').unlink(missing_ok=True)
    generate(result,cfg,[0x0000006f]);words=firmware(result,cfg,source=CHAPTER/'main_tang.c');soc=generate(result,cfg,words,rtl=True)
    gate=result/'builder/gateware';cst=(gate/'tutorial14.cst').read_text();pins=audit_cst(cst)
    negative_checks={}
    for name,text in {'duplicate-pin':cst.replace('M11;','T13;'),'wrong-voltage':cst.replace('IO_TYPE=LVCMOS33','IO_TYPE=LVCMOS18',1)}.items():
        try:audit_cst(text)
        except AssertionError as exc:negative_checks[name]=str(exc)
        else:raise AssertionError(f'{name} escaped audit')
    params=soc.crg.pll.compute_config()
    actual=cfg.reference_clk_hz*params['fdiv']/params['idiv']
    if abs(actual-cfg.sys_clk_hz)>1:raise AssertionError('PLL frequency mismatch')
    sdc=(gate/'tutorial14.sdc').read_text() if (gate/'tutorial14.sdc').exists() else ''
    # The native nextpnr build script must explicitly constrain frequency.
    script=(gate/'build_tutorial14.sh').read_text()
    if '--freq '+str(round(max(cfg.sys_clk_hz,cfg.reference_clk_hz)/1e6,3)) not in script:raise AssertionError('nextpnr timing target missing')
    rows=list(csv.reader(line for line in (result/'builder/csr.csv').read_text().splitlines() if not line.startswith('#')))
    memories={r[1]:(int(r[2],0),int(r[3])) for r in rows if r and r[0]=='memory_region'}
    if memories!=cfg.regions:raise AssertionError(f'memory map mismatch {memories}')
    logic=check_logic(result)
    rtl=result/'rtl';rtl.mkdir(exist_ok=True);sources=[]
    for path in [Path(row[0]) for row in soc.platform.sources]+list(gate.glob('*.init'))+[CHAPTER/'gowin_primitives.v',CHAPTER/'gowin_sim_primitives.v',CHAPTER/'tang_tb.sv',CHAPTER/'YOSYS_COPYING']:
        if not path.is_absolute():path=gate/path
        if path.suffix not in ('.v','.sv','.vh','.init') and path.name!='YOSYS_COPYING':continue
        target=rtl/path.name;target.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()).rstrip()+'\n')
        sources.append(dict(file=path.name,origin=str(path),source_sha256=sha(path),snapshot_sha256=sha(target),role=('primitive_library' if path.name=='gowin_primitives.v' else 'simulation_source' if path.name in ('gowin_sim_primitives.v','tang_tb.sv') else 'license' if path.name=='YOSYS_COPYING' else 'design')))
    write(rtl/'sources.json',sources);(rtl/'files.f').write_text('VexRiscv.v\ntutorial14.v\ngowin_primitives.v\n')
    (rtl/'files_sim.f').write_text('VexRiscv.v\ntutorial14.v\ngowin_sim_primitives.v\ntang_tb.sv\n')
    subprocess.run(['iverilog','-g2012','-s','tutorial14','-tnull','-f','files.f'],cwd=rtl,check=True,capture_output=True,text=True)
    constraints=result/'constraints';constraints.mkdir(exist_ok=True);shutil.copy2(gate/'tutorial14.cst',constraints/'tutorial14.cst')
    if sdc:(constraints/'tutorial14.sdc').write_text(sdc)
    (result/'pin_map.csv').write_text('port,package_pin,iostandard\n'+'\n'.join(f'{name},{pin},{std}' for name,(pin,std) in PINS.items())+'\n')
    write(result/'manifest.json',dict(board='Tang Primer 20K Dock standard',device=soc.platform.device,family=soc.platform.devicename,
          board_revision='physical PCB revision not recorded',config=cfg.values,pll={k:v for k,v in params.items() if isinstance(v,(int,float,str,bool))},pins=pins,
          firmware_sha256=sha(result/'firmware/program.bin'),sources=sources))
    write(result/'summary.json',dict(status='PASS',rtl_generation='PASS',pin_audit='PASS',rtl_elaboration='PASS',clock_target='PASS',memory_map='PASS',negative_checks=negative_checks,logic=logic,onboard='NOT_RUN: this generator does not access hardware'))
    (result/'REPORT.md').write_text(f'# Tang Primer 20K Dock：构建输入与检查\n\nPASS：完整 RTL、ROM 镜像、7 个管脚、电平、PLL 和内存图检查。\n\n参考时钟 {cfg.reference_clk_hz} Hz；系统时钟 {actual:g} Hz；UART {cfg.baud} baud。\n\nCST 两项故障注入均被捕获；RTL 可独立展开；心跳与同步逻辑仿真通过。\n\n本生成命令不执行上板；第 15 章负责综合/布局布线/bitstream，第 16、17 章记录实物结果。\n')
    print(f'PASS 14 Tang20K: 7 pins, {actual:g} Hz, complete RTL; hardware test is a separate step')

if __name__=='__main__':main()
