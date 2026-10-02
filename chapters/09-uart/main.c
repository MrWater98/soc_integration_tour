#include <stdint.h>
#include <generated/csr.h>

#define PROBE (*(volatile uint32_t *)0x80000000u)
#define FIFO_PROBE (*(volatile uint32_t *)0x80000004u)
#define DONE (*(volatile uint32_t *)0x80000ffcu)

static int exchange(uint8_t byte) {
    uint32_t limit = 10000;
    while (uart_txfull_read() && --limit) {}
    if (!limit) return 0;
    uart_rxtx_write(byte);
    limit = 10000;
    while (uart_rxempty_read() && --limit) {}
    if (!limit) return 0;
    uint8_t received = (uint8_t)uart_rxtx_read();
    PROBE = received;
    return received == byte;
}

int main(void) {
    const char text[] = "HELLO";
    const char burst[] = "123456";
    if (!exchange('U')) { DONE = 0xe1; for (;;) {} }
    for (unsigned i = 0; i < sizeof(text) - 1; i++) {
        if (!exchange((uint8_t)text[i])) { DONE = 0xe2; for (;;) {} }
    }
    uint32_t saw_full = 0;
    for (unsigned i = 0; i < sizeof(burst) - 1; i++) {
        uint32_t limit = 10000;
        while (uart_txfull_read() && --limit) saw_full = 1;
        if (!limit) { DONE = 0xe3; for (;;) {} }
        uart_rxtx_write((uint8_t)burst[i]);
    }
    if (uart_txfull_read()) saw_full = 1;
    FIFO_PROBE = saw_full;
    uint8_t last_received = 0;
    for (unsigned i = 0; i < sizeof(burst) - 1; i++) {
        uint32_t limit = 10000;
        while (uart_rxempty_read() && --limit) {}
        if (!limit) { DONE = 0xe4; for (;;) {} }
        uint8_t received = (uint8_t)uart_rxtx_read();
        last_received = received;
        PROBE = received;
        if (received != (uint8_t)burst[i]) { DONE = 0xe5; for (;;) {} }
    }
    if (!saw_full || !uart_rxempty_read()) { DONE = 0xe6; for (;;) {} }
    /* Echo the last received byte through the transmitter once more. */
    uint32_t limit = 10000;
    while (uart_txfull_read() && --limit) {}
    if (!limit) { DONE = 0xe7; for (;;) {} }
    uart_rxtx_write(last_received);
    limit = 10000;
    while (uart_rxempty_read() && --limit) {}
    if (!limit) { DONE = 0xe8; for (;;) {} }
    uint8_t echo = (uint8_t)uart_rxtx_read();
    PROBE = echo;
    if (echo != last_received) { DONE = 0xe9; for (;;) {} }
    DONE = 0x5a;
    for (;;) {}
}
