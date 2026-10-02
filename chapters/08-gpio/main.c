#include <stdint.h>
#include <generated/csr.h>

int main(void) {
    gpio_out_output_write(0x0u); /* CPU store -> CSR bridge -> GPIOOut -> output pads */
    gpio_out_output_write(0xau);

    uint32_t seen = 0;
    uint32_t saw_zero = 0;
    for (uint32_t tries = 0; tries < 10000u; tries++) {
        seen = gpio_in_input_read() & 0x0fu; /* GPIOIn status is read-only */
        if (seen == 0u && !saw_zero) {
            saw_zero = 1u;
            *(volatile uint32_t *)0x80000000u = 0u; /* CPU 已观察到初始输入 */
        }
        if (seen == 0x5u && saw_zero) {
            *(volatile uint32_t *)0x80000000u = 5u; /* CPU 已观察到变化后的输入 */
            /* Deliberately try a raw store: a read-only status must not drive the pin. */
            *(volatile uint32_t *)CSR_GPIO_IN_INPUT_ADDR = 0x0fu;
            seen = gpio_in_input_read() & 0x0fu;
            *(volatile uint32_t *)0x80000ffcu = seen == 0x5u ? 0x5au : 0xe1u;
            for (;;) {}
        }
    }
    *(volatile uint32_t *)0x80000ffcu = 0xe1u;
    for (;;) {}
}
