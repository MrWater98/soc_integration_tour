OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY {
    rom (rx)  : ORIGIN = 0x00000000, LENGTH = 4K
    sram (rw) : ORIGIN = 0x10000000, LENGTH = 4K
}
SECTIONS {
    .text : { KEEP(*(.text.init)) *(.text .text.*) *(.rodata .rodata.*) } > rom
    .data : ALIGN(4) {
        __data_start = .;
        *(.data .data.* .sdata .sdata.*)
        __data_end = .;
    } > sram AT > rom
    __data_load_start = LOADADDR(.data);
    .bss (NOLOAD) : ALIGN(4) {
        __bss_start = .;
        *(.bss .bss.* .sbss .sbss.* COMMON)
        __bss_end = .;
    } > sram
    __stack_top = ORIGIN(sram) + LENGTH(sram);
    ASSERT(__bss_end + 512 <= __stack_top, "on-chip SRAM needs 512 bytes for the stack")
    /DISCARD/ : { *(.comment) *(.eh_frame*) }
}
