#include <stdint.h>
#include <generated/csr.h>
#include <generated/soc.h>
#include "test_config.h"

#define REG(address) (*(volatile uint32_t *)(uintptr_t)(address))
#define PROBE REG(COMPLETION_BASE)
#define IRQ_PROBE REG(COMPLETION_BASE + 8)
#define IRQ_DIAG REG(COMPLETION_BASE + 12)
#define DONE REG(DONE_ADDRESS)

static volatile uint32_t initialized_word = 0x2468a135;
static volatile uint32_t irq_count;
static volatile uint32_t in_isr;
static volatile uint32_t scratch[64];
static uint32_t fault_mode;
static uint32_t workload_seed, stress_count, timer_cycles;
extern unsigned char __stack_bottom[];

/* Every byte goes through the real UART TX pin and is read from its RX FIFO. */
static void serial_char(char byte) {
    uint32_t limit = POLL_LIMIT;
    while (uart_txfull_read() && --limit) {}
    if (!limit) { DONE = 0xe4; for (;;) {} }
    uart_rxtx_write((uint8_t)byte);
    limit = POLL_LIMIT;
    while (uart_rxempty_read() && --limit) {}
    if (!limit || (uint8_t)uart_rxtx_read() != (uint8_t)byte) {
        DONE = 0xe4; for (;;) {}
    }
}

static void serial_text(const char *text) {
    while (*text) serial_char(*text++);
}

static void fail(uint32_t code) {
    serial_text("13 FAIL ");
    serial_char("0123456789ABCDEF"[(code >> 4) & 15]);
    serial_char("0123456789ABCDEF"[code & 15]);
    serial_char('\n');
    DONE = code;
    for (;;) {}
}

static void pass(unsigned stage, const char *name) {
    PROBE = stage;
    serial_text("13-0");
    serial_char('0' + stage);
    serial_char(' ');
    serial_text(name);
    serial_text(" PASS\n");
}

__attribute__((noinline)) static uint32_t fact(uint32_t n) {
    volatile uint32_t saved = n; /* retain a value across the nested call */
    if (n <= 1) return 1;
    uint32_t child = fact(n - 1);
    return saved * child;
}

static void test_rom(void) {
    const volatile uint32_t *rom = (const volatile uint32_t *)(uintptr_t)0;
    uint32_t count = ROM_BYTES / sizeof(uint32_t) - 4;
    uint32_t sum = 0;
    for (uint32_t i = 0; i < count; i++) sum += rom[i];
    if (rom[count] != 0x13c0ffee || rom[count+1] != CONFIG_TAG ||
        rom[count+2] != sum || rom[count+3] != count || PROBE != CONFIG_TAG) fail(0xe1);
    pass(1, "ROM");
}

static void boundary(volatile uint32_t *first, volatile uint32_t *last) {
    uint32_t saved_first = *first, saved_last = *last;
    *first = 0x13579bdf;
    *last = 0xeca86420;
    if (*first != 0x13579bdf || *last != 0xeca86420) fail(0xe2);
    *first = saved_first;
    *last = saved_last;
}

static void test_ram(void) {
    if (initialized_word != 0x2468a135 || irq_count || in_isr) fail(0xe2);
    for (unsigned i = 0; i < 64; i++) if (scratch[i]) fail(0xe2);
    volatile uint32_t *ram = (volatile uint32_t *)(uintptr_t)SRAM_BASE;
    for (unsigned i = 0; i < SRAM_BYTES / sizeof(uint32_t); i++) ram[i] = 0x01020304 ^ (i * 0x1021);
    for (unsigned i = 0; i < SRAM_BYTES / sizeof(uint32_t); i++)
        if (ram[i] != (0x01020304 ^ (i * 0x1021))) fail(0xe2);
    ram[0] = 0x11223344;
    *(volatile uint8_t *)(uintptr_t)(SRAM_BASE + 1) = 0xaa;
    *(volatile uint16_t *)(uintptr_t)(SRAM_BASE + 2) = 0xbbcc;
    if (ram[0] != 0xbbccaa44) fail(0xe2);
    boundary(ram, ram + SRAM_BYTES / sizeof(uint32_t) - 1);
    /* The linker reserves a guard above __stack_top for this last-word test. */
    boundary((volatile uint32_t *)(uintptr_t)MAIN_RAM_BASE,
             (volatile uint32_t *)(uintptr_t)(MAIN_RAM_BASE + MAIN_RAM_BYTES - 4));
    if (fact(6) != 720) fail(0xe2);
    REG((uintptr_t)__stack_bottom) = 0xcafef00d;
    for (unsigned i = 0; i < 64; i++) scratch[i] = 0x76543210 ^ i;
    pass(2, "RAM");
}

static void test_gpio(void) {
    if (fault_mode == 1) {
        /* Actual CPU fault: write to the read-only input CSR instead of output. */
        REG(CSR_GPIO_IN_INPUT_ADDR) = GPIO_PATTERN;
    } else gpio_out_output_write(GPIO_PATTERN);
    if (gpio_out_output_read() != GPIO_PATTERN || gpio_in_input_read() != GPIO_INPUT_PATTERN) fail(0xe3);
    pass(3, "GPIO");
}

void isr(void) {
    if (in_isr || !(timer0_ev_pending_read() & 1u)) fail(0xe9);
    in_isr = 1;
    timer0_ev_pending_write(1);
    irq_count++;
    IRQ_PROBE = irq_count;
    in_isr = 0;
}

static void disable_irq(void) {
    asm volatile ("csrci mstatus, 8");
    asm volatile ("csrw 0xbc0, zero");
    timer0_en_write(0);
    timer0_ev_enable_write(0);
    timer0_ev_pending_write(1);
}

static void start_timer(uint32_t reload) {
    timer0_en_write(0);
    timer0_load_write(timer_cycles);
    timer0_reload_write(reload);
    timer0_ev_pending_write(1);
    timer0_ev_enable_write(1);
    unsigned slot = TIMER0_INTERRUPT + (fault_mode == 2 ? 1 : 0);
    uint32_t mask = 1u << slot;
    asm volatile ("csrw 0xbc0, %0" :: "r"(mask));
    asm volatile ("csrsi mstatus, 8");
    timer0_en_write(1);
}

static void wait_irqs(uint32_t target) {
    for (uint32_t i = 0; i < POLL_LIMIT; i++) if (irq_count >= target) return;
    IRQ_DIAG = timer0_ev_pending_read();
    fail(0xe5);
}

static void test_timer(void) {
    start_timer(0);
    wait_irqs(1);
    for (volatile unsigned i = 0; i < 128; i++) asm volatile ("nop");
    disable_irq();
    if (irq_count != 1 || timer0_ev_pending_read()) fail(0xe5);
    pass(5, "TIMER");
}

static uint8_t spi_byte(uint8_t tx, uint8_t cs_n) {
    uint8_t rx = 0;
    for (int bit = 7; bit >= 0; bit--) {
        uint8_t pins = (cs_n << 2) | (((tx >> bit) & 1u) << 1);
        spi_out_write(pins);
        spi_out_write(pins | 1u);
        rx = (uint8_t)((rx << 1) | (spi_input_read() & 1u));
        spi_out_write(pins);
    }
    return rx;
}

static void check_spi(void) {
    spi_out_write(0);
    (void)spi_byte(SPI_COMMAND, 0);
    uint8_t answer = spi_byte(0, 0);
    spi_out_write(4);
    if (answer != SPI_REPLY) fail(0xe6);
}

static void i2c_start(void) { i2c_out_write(3); i2c_out_write(2); i2c_out_write(0); }
static void i2c_stop(void) { i2c_out_write(0); i2c_out_write(2); i2c_out_write(3); }
static int i2c_write_byte(uint8_t byte) {
    for (int bit = 7; bit >= 0; bit--) {
        uint32_t sda = (byte >> bit) & 1u;
        i2c_out_write(sda); i2c_out_write(2u | sda); i2c_out_write(sda);
    }
    i2c_out_write(1); i2c_out_write(3);
    int ack = !(i2c_input_read() & 1u);
    i2c_out_write(1);
    return ack;
}
static uint8_t i2c_read_byte(void) {
    uint8_t byte = 0;
    for (unsigned bit = 0; bit < 8; bit++) {
        i2c_out_write(1); i2c_out_write(3);
        byte = (uint8_t)((byte << 1) | (i2c_input_read() & 1u));
        i2c_out_write(1);
    }
    i2c_out_write(1); i2c_out_write(3); i2c_out_write(1); /* final NACK */
    return byte;
}
static void check_i2c(void) {
    for (unsigned index = 0; index < 2; index++) {
        uint8_t wanted = index ? 0xc3 : 0x5a;
        i2c_start();
        if (!i2c_write_byte(I2C_ADDRESS << 1) || !i2c_write_byte(index) || !i2c_write_byte(wanted)) fail(0xe7);
        i2c_stop();
        i2c_start();
        if (!i2c_write_byte(I2C_ADDRESS << 1) || !i2c_write_byte(index)) fail(0xe7);
        i2c_start();
        if (!i2c_write_byte((I2C_ADDRESS << 1) | 1)) fail(0xe7);
        uint8_t actual = i2c_read_byte();
        i2c_stop();
        if (actual != wanted) fail(0xe7);
    }
}

static uint32_t random_next(uint32_t *state) {
    uint32_t x = *state;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    return *state = x;
}

static void stress(void) {
    uint32_t before = irq_count, rolling = 0x12345678, rng = workload_seed;
    start_timer(timer_cycles);
    serial_text("STRESS:");
    for (unsigned i = 0; i < stress_count; i++) {
        if (workload_seed) {
            uint32_t value = random_next(&rng);
            unsigned op = value & 3u;
            /* Host independently reproduces this sequence from the seed. */
            REG(COMPLETION_BASE + 32) = value;
            serial_char('!' + (value >> 8) % 94);
            if (op == 0) {
                uint32_t wanted = (value >> 2) & GPIO_MASK;
                gpio_out_output_write(wanted);
                if (gpio_out_output_read() != wanted) fail(0xe8);
            } else if (op == 1) check_spi();
            else if (op == 2) check_i2c();
            else {
                unsigned index = (value >> 2) % (SRAM_BYTES / 4);
                unsigned lane = (value >> 16) & 3u;
                volatile uint32_t *word = (volatile uint32_t *)(uintptr_t)(SRAM_BASE + 4*index);
                *word = value;
                *(volatile uint8_t *)((uintptr_t)word + lane) = (uint8_t)(value >> 24);
                uint32_t expected_word = (value & ~(255u << (lane*8))) | ((value >> 24) << (lane*8));
                if (*word != expected_word) fail(0xe8);
            }
        } else {
            serial_char('A' + i % 26);
            gpio_out_output_write((i & 1u) ? GPIO_MASK : 0);
            if (gpio_out_output_read() != ((i & 1u) ? GPIO_MASK : 0)) fail(0xe8);
            if (i % 32 == 0) { check_spi(); check_i2c(); }
        }
        rolling = (rolling << 1) ^ (rolling >> 31) ^ i;
        if (scratch[i % 64] != (0x76543210 ^ (i % 64))) fail(0xe8);
        if (i % 32 == 0 && fact(6) != 720) fail(0xe8);
    }
    serial_char('\n');
    wait_irqs(before + MINIMUM_IRQS);
    disable_irq();
    uint32_t expected = 0x12345678;
    for (unsigned i = 0; i < stress_count; i++) expected = (expected << 1) ^ (expected >> 31) ^ i;
    if (rolling != expected || REG((uintptr_t)__stack_bottom) != 0xcafef00d ||
        initialized_word != 0x2468a135 || in_isr) fail(0xe8);
    pass(8, "CONCURRENT");
}

int main(void) {
    fault_mode = REG(COMPLETION_BASE + 4);
    workload_seed = REG(COMPLETION_BASE + 16);
    stress_count = REG(COMPLETION_BASE + 20);
    timer_cycles = REG(COMPLETION_BASE + 24);
    uart_ev_enable_write(0); /* UART IRQ has a slot, but this firmware polls RX/TX. */
    disable_irq();
    PROBE = 0;
    serial_text("13 BOOT\n");
    test_rom();
    test_ram();
    test_gpio();
    serial_text("UART: integrated loopback\n");
    pass(4, "UART");
    test_timer();
    spi_out_write(4);
    (void)spi_byte(SPI_COMMAND, 1);
    if (spi_byte(0, 1) != 0xff) fail(0xe6);
    check_spi(); pass(6, "SPI");
    i2c_start();
    int absent_ack = i2c_write_byte((I2C_ADDRESS ^ 1u) << 1);
    i2c_stop();
    if (absent_ack) fail(0xe7);
    check_i2c(); pass(7, "I2C");
    stress();
    serial_text("13 ALL PASS\n");
    DONE = 0x5a;
    for (;;) {}
}
