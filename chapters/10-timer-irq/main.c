#include <stdint.h>
#include <generated/csr.h>

#define POLL_PROBE (*(volatile uint32_t *)0x80000000u)
#define IRQ_PROBE (*(volatile uint32_t *)0x80000004u)
#define DONE (*(volatile uint32_t *)0x80000ffcu)

#define PLIC_BASE 0xf0c00000u
#define PLIC_PRIORITY (*(volatile uint32_t *)(PLIC_BASE + 4u))
#define PLIC_ENABLED (*(volatile uint32_t *)(PLIC_BASE + 0x2000u))
#define PLIC_THRESHOLD (*(volatile uint32_t *)(PLIC_BASE + 0x200000u))
#define PLIC_CLAIM (*(volatile uint32_t *)(PLIC_BASE + 0x200004u))
#define TIMER_IRQ 1u

static volatile uint32_t irq_count;
static volatile uint32_t phase;
static volatile uint32_t inside_isr;

static void fail(uint32_t code) {
    DONE = code;
    for (;;) {}
}

void isr(void) {
    uint32_t claim = PLIC_CLAIM;
    uint32_t pending = timer0_ev_pending_read();
    if (inside_isr || claim != TIMER_IRQ || !(pending & 1u)) fail(0xe1);
    inside_isr = 1;
    timer0_ev_pending_write(1);  /* Acknowledge the source before returning with mret. */
    PLIC_CLAIM = claim;
    irq_count++;
    IRQ_PROBE = (phase << 16) | irq_count;
    inside_isr = 0;
}

static void irq_enable(void) {
    PLIC_PRIORITY = 1;
    PLIC_THRESHOLD = 0;
    PLIC_ENABLED = 1u << TIMER_IRQ;
    asm volatile ("csrsi mstatus, 8");         /* Global machine interrupt enable. */
}

static void irq_disable(void) {
    asm volatile ("csrci mstatus, 8");
    PLIC_ENABLED = 0;
}

static void wait_count(uint32_t target) {
    for (uint32_t tries = 0; tries < 100000u; tries++) {
        if (irq_count >= target) return;
    }
    fail(0xe2);
}

int main(void) {
    /* First observe the countdown with all interrupts disabled. */
    timer0_ev_enable_write(0);
    timer0_en_write(0);
    timer0_load_write(600);
    timer0_reload_write(0);
    timer0_en_write(1);
    timer0_update_value_write(1);
    uint32_t first = timer0_value_read();
    for (volatile uint32_t i = 0; i < 16; i++) asm volatile ("nop");
    timer0_update_value_write(1);
    uint32_t second = timer0_value_read();
    if (first > 0xffffu || second >= first || second == 0) fail(0xe3);
    POLL_PROBE = (second << 16) | first;
    timer0_en_write(0);

    /* One-shot: exactly one interrupt, then the timer stays at zero. */
    phase = 1;
    timer0_ev_pending_write(1);
    timer0_ev_enable_write(1);
    timer0_load_write(300);
    timer0_reload_write(0);
    irq_enable();
    timer0_en_write(1);
    wait_count(1);
    for (volatile uint32_t i = 0; i < 300; i++) asm volatile ("nop");
    if (irq_count != 1) fail(0xe4);
    timer0_en_write(0);
    timer0_ev_pending_write(1);

    /* Periodic: reload every 1200 sys clocks; the ISR clears each event. */
    phase = 2;
    timer0_load_write(0);
    timer0_reload_write(1200);
    timer0_en_write(1);
    wait_count(4);
    timer0_ev_enable_write(0);
    timer0_en_write(0);
    timer0_ev_pending_write(1);
    irq_disable();
    uint32_t stopped = irq_count;
    for (volatile uint32_t i = 0; i < 500; i++) asm volatile ("nop");
    if (stopped != 4 || irq_count != stopped) fail(0xe5);
    DONE = 0x5a;
    for (;;) {}
}
