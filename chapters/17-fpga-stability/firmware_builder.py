"""Local bare-metal build; startup/linker scheme introduced in chapter 14."""
import hashlib,json,re,shutil,subprocess
from pathlib import Path
CHAPTER=Path(__file__).resolve().parent
def write(path,data):path.write_text(json.dumps(data,indent=2)+"\n")
def firmware(result,cfg,source=None):
    import litex
    out=result/'firmware';out.mkdir(exist_ok=True)
    linker=f'''OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY {{ rom(rx): ORIGIN=0, LENGTH={cfg.rom_size}
main_ram(rwx): ORIGIN=0x40000000, LENGTH={cfg.main_ram_size} }}
SECTIONS {{
.text : {{ KEEP(*(.text.init)) *(.text .text.*) *(.rodata .rodata.*) }} > rom
.data : ALIGN(4) {{ __data_start=.; *(.data .data.* .sdata .sdata.*) . = ALIGN(4); __data_end=.; }} > main_ram AT > rom
__data_load_start=LOADADDR(.data);
.bss(NOLOAD) : ALIGN(4) {{ __bss_start=.; *(.bss .bss.* .sbss .sbss.* COMMON) . = ALIGN(4); __bss_end=.; }} > main_ram
__stack_top=ORIGIN(main_ram)+LENGTH(main_ram);
__stack_bottom=__stack_top - {cfg.stack_size};
ASSERT(__bss_end<=__stack_bottom,"data overlaps stack")
/DISCARD/ : {{ *(.comment) *(.eh_frame*) }}
}}
'''
    # GNU ld requires whitespace around assignments and region separators.
    linker=re.sub(r'(?<![<>=])=(?!=)', ' = ', linker)
    linker=linker.replace('rom(rx):','rom (rx) :').replace('main_ram(rwx):','main_ram (rwx) :')
    (out/'linker.ld').write_text(linker)
    (out/'test_config.h').write_text(f'#define LED_MASK 1u\n#define STRESS_WORDS {cfg.stress_words}u\n#define TEST_SEED {cfg.seed}u\n#define INJECT_FAULT {int(cfg.inject_fault)}u\n')
    gcc=shutil.which('riscv64-unknown-elf-gcc');objcopy=shutil.which('riscv64-unknown-elf-objcopy')
    if not gcc or not objcopy:raise RuntimeError('RISC-V GCC/objcopy missing; install chapter 00 toolchain')
    base=Path(litex.__file__).resolve().parents[1]
    cmd=[gcc,'-march=rv32im','-mabi=ilp32','-mno-relax','-O1','-ffreestanding','-fno-builtin','-nostdlib','-nostartfiles',
         '-I',str(result/'builder/software/include'),'-I',str(out),'-I',str(base/'litex/soc/software/include'),
         '-I',str(base/'litex/soc/cores/cpu/vexriscv'),f'-Wl,-T,{out/"linker.ld"}',f'-Wl,-Map={out/"program.map"}',
         '-Wl,--build-id=none',str(CHAPTER/'startup.S'),str(source or CHAPTER/'main.c'),'-o',str(out/'program.elf')]
    run=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
    (out/'link.log').write_text(run.stdout+run.stderr);write(out/'compile-command.json',cmd);run.check_returncode()
    subprocess.run([objcopy,'-O','binary',str(out/'program.elf'),str(out/'program.bin')],check=True,timeout=30)
    data=(out/'program.bin').read_bytes()
    if len(data)>cfg.rom_size:raise ValueError('firmware exceeds ROM')
    data+=bytes(cfg.rom_size-len(data))
    return [int.from_bytes(data[i:i+4],'little') for i in range(0,len(data),4)]
