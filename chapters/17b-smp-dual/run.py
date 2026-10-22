#!/usr/bin/env python3
"""Real VexRiscv-SMP firmware and shared-memory simulation; no FPGA required."""
import argparse,hashlib,json,logging,os,shutil,subprocess,sys,time
from pathlib import Path
from contextlib import redirect_stdout,redirect_stderr
CHAPTER=Path(__file__).resolve().parent
ROOT=CHAPTER.parents[1]
sys.path.insert(0,str(ROOT))
from tutorial_paths import add_litex_to_path
add_litex_to_path(ROOT)
HARTS=2

def design(out,words):
 from migen import Module,ClockDomain,Memory,Signal,If,FSM,NextState,NextValue
 from litex.build.sim import SimPlatform
 from litex.build.generic_platform import Pins,Subsignal
 from litex.soc.integration.soc_core import SoCCore
 from litex.soc.integration.soc import SoCRegion
 from litex.soc.cores.cpu.vexriscv_smp.core import VexRiscvSMP as CPU
 from litex.soc.integration.builder import Builder
 CPU.cpu_count=HARTS;CPU.icache_size=CPU.dcache_size=4096 if HARTS==1 else 8192
 CPU.icache_ways=CPU.dcache_ways=1 if HARTS==1 else 2
 CPU.icache_width=CPU.dcache_width=32 if HARTS==1 else 64
 CPU.wishbone_memory=HARTS==1;CPU.coherent_dma=HARTS==2;CPU.litedram_width=128
 CPU.hardware_breakpoints=0;CPU.with_fpu=False;CPU.with_rvc=False;CPU.out_of_order_decoder=True
 platform=SimPlatform('SMP_TUTORIAL',[('sys_clk',0,Pins(1)),('sys_rst',0,Pins(1)),('serial',0, Subsignal('tx',Pins(1)),Subsignal('rx',Pins(1)))])
 soc=SoCCore(platform,clk_freq=1_000_000,cpu_type='vexriscv_smp',cpu_variant='standard',cpu_reset_address=0,
  integrated_rom_size=8192,integrated_rom_init=words,integrated_sram_size=4096,
  integrated_main_ram_size=65536 if HARTS==1 else 0,with_uart=True,uart_name='serial',uart_baudrate=100000,with_timer=False,with_ctrl=False,ident=f'Tutorial SMP {HARTS}')
 crg=Module();crg.clock_domains.cd_sys=ClockDomain('sys');crg.comb += [crg.cd_sys.clk.eq(platform.request('sys_clk')),crg.cd_sys.rst.eq(platform.request('sys_rst'))];soc.add_module('crg',crg)
 if HARTS==2:
  soc.bus.add_region('main_ram',SoCRegion(origin=0x40000000,size=65536,cached=True))
  soc.cpu.add_memory_buses(32,128)
  mem=Memory(128,4096,init=[0]*4096,name="shared_ram");soc.specials += mem
  for n,bus in enumerate(soc.cpu.memory_buses):
   mod=Module();port=mem.get_port(write_capable=True,we_granularity=8,async_read=True);mod.specials += port
   addr=Signal(12,name="native_addr"+str(n));data=Signal(128,name="native_data"+str(n))
   mod.comb += [port.adr.eq(addr),port.dat_w.eq(bus.wdata.data),port.we.eq(0)]
   fsm=FSM(reset_state='CMD');mod.submodules.fsm=fsm
   fsm.act('CMD',bus.cmd.ready.eq(bus.cmd.addr<4096),If(bus.cmd.valid & bus.cmd.ready,NextValue(addr,bus.cmd.addr),If(bus.cmd.we,NextState('WRITE')).Else(NextState('SAMPLE'))))
   fsm.act('WRITE',bus.wdata.ready.eq(1),If(bus.wdata.valid,port.we.eq(bus.wdata.we),NextState('CMD')))
   fsm.act('SAMPLE',NextValue(data,port.dat_r),NextState('READ'))
   fsm.act('READ',bus.rdata.valid.eq(1),bus.rdata.data.eq(data),If(bus.rdata.ready,NextState('CMD')))
   soc.add_module('native_ram'+str(n),mod)
 builder=Builder(soc,output_dir=str(out/'builder'),compile_software=False,compile_gateware=False)
 platform.output_dir=str(out/'builder');soc.finalize();builder._generate_includes(with_bios=False);builder._generate_csr_map()
 rtl=out/'rtl';rtl.mkdir(exist_ok=True)
 saved=Path.cwd()
 try:
  os.chdir(rtl);platform.get_verilog(soc,name='sim').write('sim.v')
 finally:os.chdir(saved)
 for row in platform.sources:
  src=Path(row[0]);src=src if src.is_absolute() else saved/src
  if src.suffix in ('.v','.sv','.vh'):shutil.copyfile(src,rtl/src.name)
 return soc

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/f'results/17{"a" if HARTS==1 else "b"}');p.add_argument('--work',type=int,default=1000);p.add_argument('--stop-hart',action='store_true');p.add_argument('--bad-mailbox',action='store_true');p.add_argument('--delay-hart',type=int,default=0);p.add_argument('--reboots',type=int,default=2);args=p.parse_args()
 if not 1<=args.work<=10000 or not 1<=args.reboots<=10 or not 0<=args.delay_hart<=10000 or (args.stop_hart and args.bad_mailbox):p.error('work 1..10000; reboots 1..10; delay 0..10000; one fault at a time')
 out=args.output.resolve();out.mkdir(parents=True,exist_ok=True);(out/'summary.json').unlink(missing_ok=True)
 with (out/'generate.log').open('w') as log,redirect_stdout(log),redirect_stderr(log):
  logging.basicConfig(stream=log,level=logging.INFO,force=True);design(out,[0x6f])
 fw=out/'firmware';fw.mkdir(exist_ok=True)
 (fw/'test_config.h').write_text(f'#define CPU_COUNT {HARTS}u\n#define WORK {args.work}u\n#define FAULT_STOP {int(args.stop_hart)}u\n#define FAULT_MAILBOX {int(args.bad_mailbox)}u\n#define DELAY_HART {args.delay_hart}u\n')
 (fw/'linker.ld').write_text('''OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY { rom (rx) : ORIGIN = 0, LENGTH = 8192
ram (rwx) : ORIGIN = 0x40001000, LENGTH = 61440 }
SECTIONS { .text : { KEEP(*(.text.init)) *(.text*) *(.rodata*) } > rom
.data : { *(.data*) } > ram AT > rom
.bss (NOLOAD) : { *(.bss*) *(.sbss*) } > ram
__stack_top = 0x40010000;
ASSERT(SIZEOF(.data)==0,"startup has no data copy")
ASSERT(SIZEOF(.bss)==0,"startup has no bss clear")
/DISCARD/ : { *(.comment) *(.eh_frame*) } }
''')
 import litex
 base=Path(litex.__file__).resolve().parents[1]
 cmd=['riscv64-unknown-elf-gcc','-march=rv32ima','-mabi=ilp32','-mno-relax','-msmall-data-limit=0','-O1','-ffreestanding','-fno-builtin','-nostdlib','-nostartfiles','-I',str(fw),'-I',str(out/'builder/software/include'),'-I',str(base/'litex/soc/software/include'),'-I',str(base/'litex/soc/cores/cpu/vexriscv_smp'),f'-Wl,-T,{fw/"linker.ld"}',f'-Wl,-Map={fw/"program.map"}',str(CHAPTER/'startup.S'),str(CHAPTER/'main.c'),'-o',str(fw/'program.elf')]
 with (fw/'compile.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
 subprocess.run(['riscv64-unknown-elf-objcopy','-O','binary',str(fw/'program.elf'),str(fw/'program.bin')],check=True)
 data=(fw/'program.bin').read_bytes();data+=bytes(8192-len(data));words=[int.from_bytes(data[i:i+4],'little') for i in range(0,len(data),4)]
 with (out/'generate.log').open('a') as log,redirect_stdout(log),redirect_stderr(log):
  logging.basicConfig(stream=log,level=logging.INFO,force=True);design(out,words)
 rtl=out/'rtl';tb=(CHAPTER/'tb.sv').read_text().replace('__REBOOTS__',str(args.reboots)).replace('__EXPECT_FAULT__',str(int(args.stop_hart or args.bad_mailbox))).replace('__FAULT_MESSAGE__','mailbox' if args.bad_mailbox else 'timeout')
 (rtl/'tb.sv').write_text(tb)
 records=[{'file':x.name,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in sorted(rtl.iterdir()) if x.suffix in ('.v','.sv','.init','.vh')]
 (rtl/'sources.json').write_text(json.dumps(records,indent=2)+'\n')
 cxx=shutil.which('g++-11') or shutil.which('g++')
 cmd=['verilator','--binary','--timing','--top-module','tb','-Wno-fatal','-j','2','-CFLAGS','-std=c++20','-MAKEFLAGS',f'CXX={cxx}','--Mdir',str(out/'obj')]+[x.name for x in sorted(rtl.iterdir()) if x.suffix in ('.v','.sv')]
 (out/'commands.json').write_text(json.dumps({'compile':cmd},indent=2)+'\n')
 compile_start=time.monotonic()
 with (out/'compile.log').open('w') as log:subprocess.run(cmd,cwd=rtl,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
 compile_seconds=time.monotonic()-compile_start;run_start=time.monotonic()
 with (out/'run.log').open('w') as log:subprocess.run([str(out/'obj/Vtb')],cwd=rtl,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
 text=(out/'run.log').read_text();expected=('SMP FAIL mailbox' if args.bad_mailbox else 'SMP FAIL timeout') if (args.stop_hart or args.bad_mailbox) else f'SMP PASS harts={HARTS:08X}'
 if text.count(expected)!=args.reboots:raise RuntimeError(text[-3000:])
 if not (args.stop_hart or args.bad_mailbox):
  for h in range(HARTS):
   marker=f'SMP HART {h:08X} count={args.work:08X} sum={args.work*(args.work+1)//2:08X}'
   if text.count(marker)!=args.reboots:raise RuntimeError('Wrong independent hart evidence '+marker)
 if not (args.stop_hart or args.bad_mailbox):
  assert text.count('SMP IRQ PASS')==args.reboots
  assert text.count('SMP TIMER PASS')==args.reboots
  assert text.count(f'SMP ATOMIC count={args.work*HARTS:08X}')==args.reboots
 report={'status':'PASS: expected fault captured' if (args.stop_hart or args.bad_mailbox) else 'PASS: real SMP RTL and independent mailbox checks','harts':HARTS,'compile_seconds':compile_seconds,'run_seconds':time.monotonic()-run_start,'work_per_hart':args.work,'delay_hart_loop_iterations':args.delay_hart,'fault_stop':args.stop_hart,'fault_mailbox':args.bad_mailbox,'checks':(['exact expected UART fault and repeated reset'] if (args.stop_hart or args.bad_mailbox) else ['per-hart RAM pattern and byte write','three CLINT software IRQs per hart','one CLINT timer IRQ per hart','atomic shared counter','independent mailboxes','system reset and repeated boot']),'reset_runs':args.reboots,'isa':'rv32ima','memory':'native shared 128-bit model, cached coherent CPU accesses' if HARTS==2 else 'Wishbone integrated RAM','fpga':'NOT_RUN','clock':'ideal 1 MHz simulation, not a measured FPGA clock','temperature_voltage':'NOT_APPLICABLE: simulation','sources':records}
 (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');(out/'REPORT.md').write_text('# SMP 实测仿真\n\n'+report['status']+'\n\n'+text+'\nFPGA 上板：NOT_RUN。\n')
 print(report['status'],out)
if __name__=='__main__':main()
