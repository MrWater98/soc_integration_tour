OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY {
    rom (rx) : ORIGIN = 0, LENGTH = 4K
    ram (rw) : ORIGIN = 0x40000000, LENGTH = MAIN_RAM_LENGTH
}
SECTIONS {
    .text : { KEEP(*(.text.init)) *(.text .text.*) *(.rodata .rodata.*) } > rom
    .data : ALIGN(4) {
        __data_start = .;
        *(.data .data.* .sdata .sdata.*)
        __data_end = .;
    } > ram AT > rom
    __data_load_start = LOADADDR(.data);
    .bss (NOLOAD) : ALIGN(4) {
        __bss_start = .;
        *(.bss .bss.* .sbss .sbss.* COMMON)
        . = ALIGN(4);
        __bss_end = .;
    } > ram
    __stack_top = ORIGIN(ram) + LENGTH(ram);
    ASSERT(__bss_end + 512 <= __stack_top, "RAM needs data plus 512-byte stack reserve")
    /DISCARD/ : { *(.comment) *(.eh_frame*) }
}
