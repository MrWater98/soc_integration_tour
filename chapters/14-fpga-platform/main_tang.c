#include <stdint.h>
#include <generated/csr.h>
#include "test_config.h"

static void character(char value) {
    while (uart_txfull_read()) {}
    uart_rxtx_write((uint8_t)value);
}
static void text(const char *value) { while (*value) character(*value++); }
static void hexadecimal(uint32_t value) {
    for (int i=7;i>=0;i--) character("0123456789ABCDEF"[(value>>(4*i))&15]);
}
int main(void) {
    uart_ev_enable_write(0);
    leds_output_write(LED_MASK);
    text("14 HELLO: CPU reached main; LEDs are mapped\r\n");
    uint32_t previous=0xffffffff;
    uint32_t alive=0;
    for (;;) {
        if (++alive == 1000000u) {
            text("14 ALIVE: Tang Primer 20K CPU polling\r\n");
            alive=0;
        }
        uint32_t buttons=buttons_input_read();
        if (buttons!=previous) {
            text("BUTTONS=0x"); hexadecimal(buttons); text("\r\n");
            previous=buttons;
        }
        /* Physical LED4 is independent heartbeat; LED5 mirrors button1. */
        leds_output_write(buttons & LED_MASK);
    }
}
