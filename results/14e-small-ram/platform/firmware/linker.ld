OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY { rom (rx) : ORIGIN = 0, LENGTH = 8192
main_ram (rwx) : ORIGIN = 0x40000000, LENGTH = 4096 }
SECTIONS {
.text : { KEEP(*(.text.init)) *(.text .text.*) *(.rodata .rodata.*) } > rom
.data : ALIGN(4) { __data_start = .; *(.data .data.* .sdata .sdata.*) .  =  ALIGN(4); __data_end = .; } > main_ram AT > rom
__data_load_start = LOADADDR(.data);
.bss(NOLOAD) : ALIGN(4) { __bss_start = .; *(.bss .bss.* .sbss .sbss.* COMMON) .  =  ALIGN(4); __bss_end = .; } > main_ram
__stack_top = ORIGIN(main_ram)+LENGTH(main_ram);
__stack_bottom = __stack_top - 1024;
ASSERT(__bss_end<=__stack_bottom,"data overlaps stack")
/DISCARD/ : { *(.comment) *(.eh_frame*) }
}
