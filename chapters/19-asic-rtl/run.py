#!/usr/bin/env python3
"""Generate a cache-free LiteX core, enumerate/map every memory, simulate it."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT/'external/fpga-tools/oss-cad-suite/bin'
IVERILOG = str(TOOLS/'iverilog') if (TOOLS/'iverilog').exists() else 'iverilog'
VVP = str(TOOLS/'vvp') if (TOOLS/'vvp').exists() else 'vvp'
sys.path.insert(0, str(ROOT))
from tutorial_paths import add_litex_to_path


def run(command, out, name, timeout=300, cwd=None):
    result = subprocess.run(list(map(str, command)), cwd=cwd, capture_output=True,
                            text=True, timeout=timeout)
    (out/name).write_text(result.stdout+result.stderr)
    if result.returncode:
        raise RuntimeError(f'{name}: command failed ({result.returncode}); see {out/name}')
    return result.stdout+result.stderr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results/19')
    parser.add_argument('--ram-bytes', type=int, default=2048)
    parser.add_argument('--map-cells', action='store_true', help='Also map to pinned ICS55 RVT cells')
    args = parser.parse_args()
    if args.ram_bytes not in (1024, 2048, 4096):
        parser.error('This flip-flop RAM pilot allows only 1024, 2048, or 4096 bytes')
    out=args.output.resolve(); out.mkdir(parents=True,exist_ok=True)
    (out/'summary.json').unlink(missing_ok=True)
    rtl=out/'rtl';rtl.mkdir(exist_ok=True)
    for old in rtl.iterdir():
        if old.suffix in ('.v','.init','.json'):old.unlink()
    add_litex_to_path(ROOT)
    from litex.build.sim import SimPlatform
    from litex.build.generic_platform import Pins
    from litex.soc.integration.builder import Builder
    from litex import get_data_mod
    from soc import TutorialSoC
    firmware=out/'firmware'; firmware.mkdir(exist_ok=True)
    run(['riscv64-unknown-elf-gcc','-march=rv32i','-mabi=ilp32','-mno-relax',
         '-O1','-ffreestanding','-fno-builtin','-nostdlib','-nostartfiles',
         f'-Wl,-T,{HERE/"linker.ld"}',f'-Wl,--defsym=MAIN_RAM_LENGTH={args.ram_bytes}',
         f'-Wl,-Map={firmware/"program.map"}', '-Wl,--build-id=none',
         HERE/'startup.S',HERE/'main.c','-o',firmware/'program.elf'],out,'firmware.log')
    run(['riscv64-unknown-elf-objcopy','-O','binary',firmware/'program.elf',firmware/'program.bin'],out,'objcopy.log')
    (firmware/'disassembly.txt').write_text(run(['riscv64-unknown-elf-objdump','-dh',firmware/'program.elf'],out,'objdump.log'))
    data=(firmware/'program.bin').read_bytes()
    if len(data)>4096: raise ValueError('ROM firmware overflow')
    data+=b'\0'*((-len(data))%4)
    words=[int.from_bytes(data[i:i+4],'little') for i in range(0,len(data),4)]
    class ASICPlatform(SimPlatform):
        def get_verilog(self, *vargs, **kwargs):
            kwargs['regs_init'] = True
            return super().get_verilog(*vargs, **kwargs)

    platform=ASICPlatform('ASIC_CORE',[
        ('clk',0,Pins(1)),('reset_n',0,Pins(1)),('gpio_in',0,Pins(4)),
        ('gpio_out',0,Pins(4)),('uart_tx',0,Pins(1)),('result',0,Pins(32)),('stage',0,Pins(8))])
    for name in ('reset_sync.v','peripheral.v'): platform.add_source(str(HERE/name))
    soc=TutorialSoC(platform,words,args.ram_bytes,4,8)
    builder=Builder(soc,output_dir=str(out/'builder'),compile_software=False)
    builder.build(build_name='asic_soc',run=False)
    gate=out/'builder/gateware'
    for file in [gate/'asic_soc.v',*gate.glob('*.init'),HERE/'reset_sync.v',HERE/'peripheral.v',
                 Path(get_data_mod('cpu','vexriscv').data_location)/'VexRiscv_Min.v']:
        shutil.copyfile(file,rtl/file.name)
    # The trace control added by SimPlatform is a simulator signal, not a chip pad.
    # Tie it off in the RTL testbench through an explicit port connection below.
    sources=[rtl/'asic_soc.v',rtl/'VexRiscv_Min.v',rtl/'reset_sync.v',rtl/'peripheral.v']
    # Lower behavioral processes before event-driven simulation. This also
    # resolves LiteX's undriven reset-valued constant signals into constants.
    normalization='\n'.join('read_verilog '+str(p) for p in sources)+f'\nhierarchy -check -top asic_soc\nproc\nopt\nwrite_verilog -noattr {rtl}/elaborated.v\n'
    (out/'normalize.ys').write_text(normalization)
    run(['yosys','-s',out/'normalize.ys'],out,'normalize.log',cwd=rtl)
    run([IVERILOG,'-g2012','-s','tb','-o',out/'rtl.vvp',rtl/'elaborated.v',HERE/'tb.sv'],out,'compile.log')
    sim=run([VVP,out/'rtl.vvp'],out,'simulation.log',cwd=rtl)
    if 'PASS19' not in sim: raise RuntimeError('Missing RTL completion')
    yosys=shutil.which('yosys')
    # Inventory before memory_map retains widths, depths, read/write ports and INIT.
    common='\n'.join('read_verilog '+str(p) for p in sources)+'\nhierarchy -check -top asic_soc\nproc\nopt\nmemory_collect\n'
    (out/'inventory.ys').write_text(common+f'write_json {out}/memories.json\n')
    run([yosys,'-s',out/'inventory.ys'],out,'inventory.log',cwd=rtl)
    design=json.loads((out/'memories.json').read_text())
    memories=[]
    for module_name,module in design['modules'].items():
        for name,cell in module.get('cells',{}).items():
            if cell['type'] not in ('$mem_v2','$mem'):continue
            p=cell['parameters']
            integer=lambda key:int(p[key],2)
            memories.append(dict(module=module_name,name=name,width=integer('WIDTH'),
                depth=integer('SIZE'),read_ports=integer('RD_PORTS'),write_ports=integer('WR_PORTS'),
                read_clocked=p.get('RD_CLK_ENABLE'),write_clocked=p.get('WR_CLK_ENABLE'),
                init_defined_bits=sum(c in '01' for c in p['INIT']),
                implementation='constant logic' if integer('WR_PORTS')==0 else 'flip-flops + multiplexers'))
    if not memories:raise RuntimeError('Empty memory inventory')
    (out/'memory-inventory.json').write_text(json.dumps(memories,indent=2)+'\n')
    synthesis=common+f'''memory_map
opt
synth -top asic_soc -flatten
delete t:$scopeinfo
setattr -unset init w:*
check -assert
write_json {out}/generic.json
write_verilog -noattr {rtl}/generic.v
stat
'''
    (out/'synth.ys').write_text(synthesis)
    run([yosys,'-s',out/'synth.ys'],out,'synthesis.log',timeout=600,cwd=rtl)
    generic=json.loads((out/'generic.json').read_text())
    cells=generic['modules']['asic_soc']['cells']
    forbidden=[c['type'] for c in cells.values() if not c['type'].startswith('$_')]
    if forbidden:raise RuntimeError(f'Unmapped cells: {set(forbidden)}')
    run([IVERILOG,'-g2012','-s','tb','-o',out/'generic.vvp',rtl/'generic.v',HERE/'tb.sv'],out,'generic-compile.log')
    mapped_sim=run([VVP,out/'generic.vvp'],out,'generic-simulation.log',timeout=300,cwd=rtl)
    if 'PASS19' not in mapped_sim:raise RuntimeError('Missing mapped completion')
    area=None
    pdk_info={}
    if args.map_cells:
        base=ROOT/'external/icsprout55-pdk/IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CR'
        lib=base/'liberty/ics55_LLSC_H7CR_typ_tt_1p2_25_nldm.lib'
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT/'external/icsprout55-pdk',text=True).strip()
        if commit!='ebc3f7e5d22a67f9423e0d980cd056291a58f307':raise RuntimeError('Unexpected PDK revision')
        pdk_info=dict(commit=commit,liberty=lib.name,liberty_sha256=hashlib.sha256(lib.read_bytes()).hexdigest())
        script=synthesis+f'dfflibmap -liberty {lib}\nabc -liberty {lib}\nread_liberty -lib {lib}\nclean\ncheck -assert\nstat -liberty {lib}\nwrite_verilog -noattr -noexpr {rtl}/mapped.v\nwrite_json {out}/mapped.json\n'
        (out/'map.ys').write_text(script)
        text=run([yosys,'-s',out/'map.ys'],out,'mapping.log',timeout=900,cwd=rtl)
        shutil.copyfile(base/'verilog/ics55_LLSC_H7CR.v',rtl/'ics55_LLSC_H7CR.v')
        run([IVERILOG,'-g2012','-Dfunctional','-s','tb','-o',out/'mapped.vvp',rtl/'mapped.v',rtl/'ics55_LLSC_H7CR.v',HERE/'tb.sv'],out,'mapped-compile.log')
        mapped_sim=run([VVP,out/'mapped.vvp'],out,'mapped-simulation.log',timeout=300,cwd=rtl)
        if 'PASS19' not in mapped_sim:raise RuntimeError('Missing ICS55 completion')
        area=re.findall(r'Chip area[^:]*:\s*([0-9.]+)',text)
    io_model=ROOT/'external/icsprout55-pdk/IP/IO/ICsprout_55LLULP1233_IO_251013/verilog/icsIOA_N55_3P3.v'
    shutil.copyfile(io_model,rtl/io_model.name)
    run([IVERILOG,'-g2012','-s','tb','-o',out/'pad.vvp',io_model,HERE/'pad_pilot.sv'],out,'pad-compile.log')
    run([VVP,out/'pad.vvp'],out,'pad-simulation.log')
    files=[dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(rtl.iterdir()) if p.suffix in ('.v','.init')]
    (rtl/'sources.json').write_text(json.dumps(dict(top='asic_soc',source_files=[p.name for p in sources],files=files,simulation_inputs={'rtl':['elaborated.v'],'generic':['generic.v'],'mapped':['mapped.v','ics55_LLSC_H7CR.v'] if args.map_cells else []},working_directory='this rtl directory for .init lookup'),indent=2)+'\n')
    counts={}
    for cell in cells.values(): counts[cell['type']]=counts.get(cell['type'],0)+1
    summary=dict(status='PASS bounded ASIC core pilot',cpu='VexRiscv minimal RV32I cache-free',
        ram_bytes=args.ram_bytes,rom_bytes=4096,sram_bytes=256,uart_div=8,gpio_width=4,
        firmware_bytes=len(data),memory_bits=sum(m['width']*m['depth'] for m in memories),
        memories=memories,generic_cell_counts=counts,generic_cells=len(cells),
        ics55_mapped=args.map_cells,area_report=area,pdk=pdk_info,
        pad_cell_function='PASS actual PBMUX 0/1/Z; no timing/ESD qualification',physical_pad_ring='PENDING',sram_macro='NOT_USED: bounded flip-flop implementation',
        production_release='NOT_READY: IO/power/package/DFT/physical signoff remain')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'REPORT.md').write_text('# 19 ASIC核心适配结果\n\n'+summary['status']+'\n\n- CPU：'+summary['cpu']+'\n- main RAM：'+str(args.ram_bytes)+'字节\n- Memory总位数：'+str(summary['memory_bits'])+'\n- 通用单元数：'+str(summary['generic_cells'])+'\n- 工艺映射：'+str(args.map_cells)+'\n\n详细输入哈希见rtl/sources.json；功能日志见simulation.log、generic-simulation.log及可选mapped-simulation.log。完整pad ring、制造宏、生产DFT和物理签核尚未完成。\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
