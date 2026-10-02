#include <stdint.h>

#define PROBE (*(volatile uint32_t *)0x80000000u)
#define DONE (*(volatile uint32_t *)0x80000ffcu)
#define FLASH ((volatile uint32_t *)0xa0000000u)

static void fail(uint32_t code) { DONE = code; for (;;) {} }

int main(void) {
    if (FLASH[0] != 0x46434f53u) fail(0xe1); /* bytes: 'S','O','C','F' */
    if (FLASH[1] != 256u) fail(0xe2);        /* image length in bytes */
    PROBE = FLASH[0];

    uint32_t checksum = 0;
    for (uint32_t word = 0; word < 63; word++) {
        uint32_t data = FLASH[word];
        checksum += data & 0xffu;
        checksum += (data >> 8) & 0xffu;
        checksum += (data >> 16) & 0xffu;
        checksum += (data >> 24) & 0xffu;
    }
    if (checksum != FLASH[63]) fail(0xe3);
    PROBE = checksum;
    if (FLASH[1023] != 0xffffffffu) fail(0xe4); /* 4 KiB window last word */
    DONE = 0x5a;
    for (;;) {}
}
