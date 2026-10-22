OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY {
    rom (rx)  : ORIGIN = 0x00000000, LENGTH = 4K
    sram (rw) : ORIGIN = 0x10000000, LENGTH = 4K
    main_ram (rwx) : ORIGIN = 0x40000000, LENGTH = DEFINED(MAIN_RAM_LENGTH) ? MAIN_RAM_LENGTH : 16K
}
SECTIONS {
    .text : {
        KEEP(*(.text.init))
        *(.text .text.*)
        *(.rodata .rodata.*)
    } > rom
    .data : ALIGN(4) {
        __data_start = .;
        *(.data .data.* .sdata .sdata.*)
        __data_end = .;
    } > main_ram AT > rom
    __data_load_start = LOADADDR(.data);
    .bss (NOLOAD) : ALIGN(4) {
        __bss_start = .;
        *(.bss .bss.* .sbss .sbss.* COMMON)
        __bss_end = .;
    } > main_ram
    __stack_top = ORIGIN(main_ram) + LENGTH(main_ram);
    __heap_start = __bss_end;
    __heap_end = __stack_top - 256;
    ASSERT(__bss_end + 256 <= __stack_top, "main RAM has no room for sections and 256-byte stack margin")
    /DISCARD/ : { *(.comment) *(.eh_frame*) }
}
