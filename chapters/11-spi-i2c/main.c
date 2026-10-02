#include <stdint.h>
#include <generated/csr.h>

#define PROBE (*(volatile uint32_t *)0x80000000u)
#define DONE (*(volatile uint32_t *)0x80000ffcu)

static void fail(uint32_t code) { DONE = code; for (;;) {} }

/* SPI mode 0: set MOSI while CLK low; the slave samples on the rising edge. */
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

static void i2c_start(void) {
    i2c_out_write(3); /* both released */
    i2c_out_write(2); /* SDA falls while SCL high */
    i2c_out_write(0); /* now pull SCL low */
}

static void i2c_stop(void) {
    i2c_out_write(0);
    i2c_out_write(2); /* SCL rises while SDA low */
    i2c_out_write(3); /* SDA rises while SCL high */
}

static int i2c_write_byte(uint8_t value) {
    for (int bit = 7; bit >= 0; bit--) {
        uint32_t sda = (value >> bit) & 1u;
        i2c_out_write(sda);
        i2c_out_write(2u | sda);
        i2c_out_write(sda);
    }
    i2c_out_write(1); /* release SDA for device ACK */
    i2c_out_write(3);
    int ack = !(i2c_input_read() & 1u);
    i2c_out_write(1);
    return ack;
}

static uint8_t i2c_read_byte(void) {
    uint8_t value = 0;
    for (unsigned bit = 0; bit < 8; bit++) {
        i2c_out_write(1); /* release SDA, SCL low */
        i2c_out_write(3);
        value = (uint8_t)((value << 1) | (i2c_input_read() & 1u));
        i2c_out_write(1);
    }
    i2c_out_write(1); /* master NACK: leave SDA released on ninth clock */
    i2c_out_write(3);
    i2c_out_write(1);
    return value;
}

static void i2c_write_reg(uint8_t index, uint8_t value) {
    i2c_start();
    if (!i2c_write_byte(0x84) || !i2c_write_byte(index) ||
        !i2c_write_byte(value)) fail(0xe2);
    i2c_stop();
}

static uint8_t i2c_read_reg(uint8_t index) {
    i2c_start();
    if (!i2c_write_byte(0x84) || !i2c_write_byte(index)) fail(0xe3);
    i2c_start(); /* repeated START: retain device register pointer */
    if (!i2c_write_byte(0x85)) fail(0xe4);
    uint8_t value = i2c_read_byte();
    i2c_stop();
    return value;
}

int main(void) {
    spi_out_write(4); /* CS high, CLK low */
    (void)spi_byte(0x9f, 1); /* wrong CS: device must ignore it */
    if (spi_byte(0x00, 1) != 0xff) fail(0xe1);
    PROBE = 0x1100;
    spi_out_write(0); /* select device */
    (void)spi_byte(0x9f, 0);
    uint8_t spi_rx = spi_byte(0x00, 0);
    spi_out_write(4); /* release CS */
    if (spi_rx != 0xa5) fail(0xe5);
    PROBE = 0x1100 | spi_rx;

    i2c_out_write(3); /* idle open-drain bus: pull-up makes both lines high */
    i2c_start();
    int bad_ack = i2c_write_byte(0x86); /* 7-bit address 0x43, absent */
    i2c_stop();
    if (bad_ack) fail(0xe6);
    PROBE = 0x1200;

    i2c_write_reg(0, 0x5a);
    i2c_write_reg(1, 0xc3);
    uint8_t first = i2c_read_reg(0);
    uint8_t second = i2c_read_reg(1);
    PROBE = 0x130000 | ((uint32_t)second << 8) | first;
    if (first != 0x5a || second != 0xc3) fail(0xe7);
    PROBE = 0x120000 | ((uint32_t)second << 8) | first;
    DONE = 0x5a;
    for (;;) {}
}
