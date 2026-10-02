#include <stdint.h>

#define PROBE (*(volatile uint32_t *)0x80000000u)
#define DONE (*(volatile uint32_t *)0x80000ffcu)
#define EXT ((volatile uint32_t *)0x90000000u)

static void fail(uint32_t code) { DONE = code; for (;;) {} }

int main(void) {
    EXT[0] = 0x11223344u;
    if (EXT[0] != 0x11223344u) fail(0xe1);
    PROBE = EXT[0];

    /* Byte lane 1 of a 32-bit word is at byte offset 1 on this little-endian CPU. */
    ((volatile uint8_t *)EXT)[1] = 0xaau;
    if (EXT[0] != 0x1122aa44u) fail(0xe2);
    PROBE = EXT[0];

    EXT[1023] = 0x55667788u; /* Last 32-bit word of the 4 KiB window. */
    if (EXT[1023] != 0x55667788u) fail(0xe3);
    PROBE = EXT[1023];

    for (uint32_t i = 0; i < 8; i++) EXT[10 + i] = 0xa5000000u | i;
    for (uint32_t i = 0; i < 8; i++)
        if (EXT[10 + i] != (0xa5000000u | i)) fail(0xe4);
    PROBE = 8;
    DONE = 0x5a;
    for (;;) {}
}
