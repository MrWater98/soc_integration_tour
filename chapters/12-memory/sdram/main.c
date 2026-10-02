#include <stdint.h>
#include <generated/csr.h>
#include <generated/sdram_phy.h>

#define PROBE (*(volatile uint32_t *)0x80000000u)
#define DONE (*(volatile uint32_t *)0x80000ffcu)
#define DRAM ((volatile uint32_t *)0x40000000u)
#define LAST_WORD ((4u * 1024u * 1024u / 4u) - 1u)

static void fail(uint32_t code) { DONE = code; for (;;) {} }

int main(void) {
    /* Keep stack and C variables in on-chip SRAM until SDRAM is initialized. */
    sdram_dfii_control_write(DFII_CONTROL_CKE | DFII_CONTROL_ODT | DFII_CONTROL_RESET_N);
    init_sequence();
    sdram_dfii_control_write(DFII_CONTROL_SEL); /* Hand DFI control to LiteDRAM controller. */
    PROBE = 1;

    DRAM[0] = 0x12345678u;
    DRAM[1] = 0xa5a55a5au;
    DRAM[LAST_WORD] = 0x55aa33ccu;
    if (DRAM[0] != 0x12345678u || DRAM[1] != 0xa5a55a5au ||
        DRAM[LAST_WORD] != 0x55aa33ccu) fail(0xe1);
    PROBE = 2;

    for (uint32_t i = 0; i < 16; i++) DRAM[32+i] = 0xc0010000u | i;
    cdelay(20000); /* Much longer than tREFI; controller must refresh in this interval. */
    for (uint32_t i = 0; i < 16; i++)
        if (DRAM[32+i] != (0xc0010000u | i)) fail(0xe2);
    if (DRAM[0] != 0x12345678u || DRAM[LAST_WORD] != 0x55aa33ccu) fail(0xe3);
    PROBE = 3;
    DONE = 0x5a;
    for (;;) {}
}
