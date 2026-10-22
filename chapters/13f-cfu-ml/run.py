#!/usr/bin/env python3
"""Pinned upstream CFU -> direct RTL tests -> real VexRiscv custom instructions."""
import argparse
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import json
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT/'external/fpga-tools/oss-cad-suite/bin'
IVERILOG = str(TOOLS/'iverilog') if (TOOLS/'iverilog').exists() else 'iverilog'
VVP = str(TOOLS/'vvp') if (TOOLS/'vvp').exists() else 'vvp'
sys.path.insert(0,str(ROOT))
from tutorial_paths import add_litex_to_path
from litex_builder import build_and_run


def command(args, output, log, cwd=None):
    result=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True,timeout=120)
    text=result.stdout+result.stderr
    (output/log).write_text(text)
    result.check_returncode()
    if 'FATAL:' in text:raise RuntimeError(log)
    return text


def check_upstream():
    manifest=json.loads((HERE/'upstream/manifest.json').read_text())
    for row in manifest['files']:
        if hashlib.sha256((HERE/'upstream'/row['file']).read_bytes()).hexdigest()!=row['sha256']:
            raise RuntimeError(f'Upstream source modified: {row["file"]}')
    return manifest


def make_vectors(out,count,seed):
    rng=random.Random(seed)
    acc=0
    rows=[]
    def emit(fid,a,b,hold):
        nonlocal acc
        def s8(word,lane):
            byte=(word>>(8*lane))&255
            return byte if byte<128 else byte-256
        if fid>>3:acc=0
        else:acc=(acc+sum((s8(a,i)+128)*s8(b,i) for i in range(4)))&0xffffffff
        rows.append(f'{fid:03x} {a:08x} {b:08x} {acc:08x} {hold}\n')
    emit(8,0,0,2)
    emit(0,0x84838281,0x0103ff02,4)
    emit(0,0x80808080,0x7f7f7f7f,7)
    emit(0,0x7f7f7f7f,0x80808080,0)
    for i in range(count):
        fid=(rng.randrange(1,128)<<3) if i%19==0 else rng.randrange(8)
        emit(fid,rng.getrandbits(32),rng.getrandbits(32),rng.randrange(8))
    if {int(row.split()[-1]) for row in rows} != set(range(8)) and count>=100:
        raise RuntimeError('Random vectors did not cover every response hold length')
    (out/'vectors.txt').write_text(''.join(rows))
    return len(rows)


def direct_tests(out,count,seed):
    out.mkdir(parents=True,exist_ok=True)
    total=make_vectors(out,count,seed)
    rtl=out.parent/'rtl'/'direct';rtl.mkdir(parents=True,exist_ok=True)
    for source in (HERE/'upstream/cfu_mac.v',HERE/'upstream/cfu_passthrough.v',HERE/'tb_mac.sv',HERE/'tb_passthrough.sv'):
        shutil.copyfile(source,rtl/source.name)
    (rtl/'sources.json').write_text(json.dumps(dict(experiments={'mac':['cfu_mac.v','tb_mac.sv'],
        'passthrough':['cfu_passthrough.v','tb_passthrough.sv']},files=[dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest())
        for f in sorted(rtl.iterdir()) if f.suffix in ('.v','.sv')]),indent=2)+'\n')
    command([IVERILOG,'-g2012','-s','tb','-o',out/'passthrough.vvp',
             HERE/'upstream/cfu_passthrough.v',HERE/'tb_passthrough.sv'],out,'passthrough-compile.log')
    text=command([VVP,out/'passthrough.vvp'],out,'passthrough.log',cwd=out)
    if 'PASS_PASSTHROUGH' not in text:raise RuntimeError('Passthrough did not complete')
    command([IVERILOG,'-g2012','-s','tb','-o',out/'mac.vvp',
             HERE/'upstream/cfu_mac.v',HERE/'tb_mac.sv'],out,'mac-compile.log')
    text=command([VVP,out/'mac.vvp'],out,'mac.log',cwd=out)
    if 'PASS_MAC' not in text:raise RuntimeError('MAC did not complete')
    # Check the checker: removing +128 must break the known mathematical example.
    mutated=(HERE/'upstream/cfu_mac.v').read_text().replace("$signed(9'd128)","$signed(9'd0)")
    if mutated==(HERE/'upstream/cfu_mac.v').read_text():raise RuntimeError('Mutation did not apply')
    (rtl/'bad_offset.v').write_text(mutated)
    metadata=json.loads((rtl/'sources.json').read_text())
    metadata['experiments']['bad_offset']=['bad_offset.v','tb_mac.sv']
    metadata['files']=[row for row in metadata['files'] if row['file']!='bad_offset.v']
    metadata['files'].append(dict(file='bad_offset.v',sha256=hashlib.sha256(mutated.encode()).hexdigest()))
    (rtl/'sources.json').write_text(json.dumps(metadata,indent=2)+'\n')
    shutil.copyfile(HERE/'upstream/LICENSE.apache2',rtl/'LICENSE.cfu')
    command([IVERILOG,'-g2012','-s','tb','-o',out/'bad.vvp',rtl/'bad_offset.v',HERE/'tb_mac.sv'],out,'bad-compile.log')
    bad=out/'negative';bad.mkdir(exist_ok=True)
    shutil.copyfile(out/'vectors.txt',bad/'vectors.txt')
    result=subprocess.run([VVP,str(out/'bad.vvp')],cwd=bad,capture_output=True,text=True,timeout=30)
    (bad/'run.log').write_text(result.stdout+result.stderr)
    if 'MAC_MISMATCH' not in result.stdout+result.stderr:raise RuntimeError('Wrong offset escaped checker')
    return dict(vectors=total,random_vectors=count,seed=seed,passthrough_cases=8,
                tested_hold_cycles=sorted({int(line.split()[-1]) for line in (out/'vectors.txt').read_text().splitlines()}),
                backpressure='PASS stable through all tested hold cycles',reset_recovery='PASS',bad_offset='DETECTED')


def build_firmware(name,software):
    out=ROOT/'results'/name/'firmware';out.mkdir(parents=True,exist_ok=True)
    elf=out/'program.elf'
    args=['riscv64-unknown-elf-gcc','-march=rv32im','-mabi=ilp32','-mno-relax',
          '-O1','-ffreestanding','-fno-builtin','-nostdlib','-nostartfiles',
          '-I',HERE/'upstream',f'-Wl,-T,{HERE/"linker.ld"}',
          '-Wl,--defsym=MAIN_RAM_LENGTH=16384',f'-Wl,-Map={out/"program.map"}',
          '-Wl,--build-id=none']
    if software:args+=['-DCFU_SOFTWARE_DEFINED']
    args+=[HERE/'startup.S',HERE/'main.c',HERE/'software_cfu.c','-o',elf]
    command(args,out,'compile.log')
    command(['riscv64-unknown-elf-objcopy','-O','binary',elf,out/'program.bin'],out,'objcopy.log')
    command(['riscv64-unknown-elf-objdump','-dh',elf],out,'disassembly.txt')
    data=(out/'program.bin').read_bytes()
    if len(data)>4096:raise RuntimeError('Firmware exceeds 4KiB ROM')
    data=data.ljust(4096,b'\0')
    words=[int.from_bytes(data[i:i+4],'little') for i in range(0,len(data),4)]
    (out/'program.hex').write_text(''.join(f'{w:08x}\n' for w in words))
    # Count actual CUSTOM0 opcodes in .text, not arbitrary data bytes.
    dis=(out/'disassembly.txt').read_text()
    custom=sum((int(word,16)&127)==0x0b for word in re.findall(r'^\s*[0-9a-f]+:\s+([0-9a-f]{8})',dis,re.M))
    if (custom==0)!=software:raise RuntimeError(f'Unexpected custom opcode count: {custom}')
    return words,custom


def cpu_test(name,software):
    words,custom=build_firmware(name,software)
    add_litex_to_path(ROOT)
    from soc import TutorialSoC
    out=ROOT/'results'/name;out.mkdir(parents=True,exist_ok=True)
    with (out/'generation.log').open('w') as log,redirect_stdout(log),redirect_stderr(log):
        build_and_run(root=ROOT,chapter=name,expected='CFU_COMPLETE code=0x0000005a',
            soc=lambda platform:TutorialSoC(platform,rom_words=words),
            regions={'rom':(0,4096),'sram':(0x10000000,4096),
                     'main_ram':(0x40000000,16384),'trace':(0x80000000,64),'csr':(0xf0000000,65536)})
    text=(out/'run.log').read_text()
    if 'CFU_FAIL' in text:raise RuntimeError('Firmware failure')
    commands=int(re.search(r'CFU_COMPLETE .*commands=(\d+)',text).group(1))
    expected_commands=0 if software else 8+sum(1+(1+t%17+3)//4 for t in range(64))+64*3+64*3
    if commands!=expected_commands:raise RuntimeError(f'Unexpected CFU command count: {commands} != {expected_commands}')
    responses=int(re.search(r'CFU_COMPLETE .*responses=(\d+)',text).group(1))
    if responses!=commands:raise RuntimeError('CFU accepted command/response counts differ')
    if not all(s in text for s in ('CFU_DOT result=13','CFU_DENSE_0 result=28','CFU_DENSE_1 result=0','CFU_RANDOM_CHECKS count=64')):
        raise RuntimeError('Missing neural operator evidence')
    cycles={label:int(re.search(rf'{label} value=(\d+)',text).group(1)) for label in (
        'CFU_CPU_REFERENCE_CYCLES','CFU_ACCEL_CYCLES','CFU_PREPACKED_CYCLES')}
    rtl=out/'rtl'
    shutil.copyfile(HERE/'upstream/LICENSE.apache2',rtl/'LICENSE.cfu')
    (rtl/'sources.json').write_text(json.dumps(dict(top='sim',files=[dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted(rtl.iterdir()) if f.suffix in ('.v','.init')]),indent=2)+'\n')
    record=dict(mode='software emulator' if software else 'real CPU+CFU RTL',custom_opcodes=custom,
                accepted_cfu_commands=commands,accepted_cfu_responses=responses,cycles_64_iterations=cycles,
                dot=13,dense_relu=[28,0],random_dot_checks=64)
    (out/'cpu-summary.json').write_text(json.dumps(record,indent=2)+'\n')
    return record


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vectors',type=int,default=2000)
    p.add_argument('--seed',type=int,default=13)
    p.add_argument('--direct-only',action='store_true')
    a=p.parse_args()
    if not 1<=a.vectors<=100000:p.error('vectors must be 1..100000')
    manifest=check_upstream()
    out=ROOT/'results'/('13f-direct' if a.direct_only else '13f');out.mkdir(parents=True,exist_ok=True)
    (out/'summary.json').unlink(missing_ok=True)
    direct=direct_tests(out/'direct',a.vectors,a.seed)
    cpu=[] if a.direct_only else [cpu_test('13f',False),cpu_test('13f-software',True)]
    summary=dict(status='PASS direct CFU RTL only' if a.direct_only else 'PASS neural operator CPU+CFU experiment',
                 upstream_commit=manifest['commit'],direct=direct,cpu=cpu,
                 integration='upstream unmodified CFU and headers in chapter-local LiteX harness',
                 tflm_full_model='NOT_RUN',fpga_board='NOT_RUN',asic='NOT_RUN')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'REPORT.md').write_text('# 13F CFU神经网络算子实验\n\n'+summary['status']+'\n\n- 上游固定提交：'+manifest['commit']+'\n- 独立RTL向量：'+str(direct['vectors'])+'\n- 背压、复位恢复和错误offset检测通过\n- CPU结果和周期数见summary.json\n\n完整TFLM模型、Tang上板、ASIC实现尚未执行。\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
