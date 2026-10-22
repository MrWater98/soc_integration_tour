#include <stdint.h>
#define REG(n) (*(volatile uint32_t *)(0x80000000u + 4u*(n)))
volatile uint32_t initialized_data = 0x11223344;
volatile uint32_t zero_initialized, irq_count;
volatile uint32_t scratch[32];
extern void trap_entry(void);
extern char __stack_top[];
static void fail(uint32_t code) { REG(6)=code; for(;;){} }
void timer_isr(void) {
    uint32_t cause;
    __asm__ volatile("csrr %0, mcause" : "=r"(cause));
    if(cause != 0x8000000bu || !(REG(5)&1)) fail(0xe8);
    REG(5)=1; /* W1C: clear the peripheral source, not just the CPU enable. */
    irq_count++;
}
__attribute__((noinline)) static uint32_t stack_test(uint32_t n) {
    volatile uint32_t local[4]={n,n+1,n+2,n+3};
    return local[0]+local[3];
}
int main(void) {
    REG(7)=1;
    if(initialized_data!=0x11223344 || zero_initialized || scratch[0] || irq_count) fail(0xe1);
    REG(7)=2;
    /* Stack occupies RAM's high end; test the low global buffer separately. */
    for(unsigned i=0;i<32;i++) scratch[i]=0x5a5a0000u+i;
    for(unsigned i=0;i<32;i++) if(scratch[i] != 0x5a5a0000u+i) fail(0xe2);
    volatile uint8_t *bytes=(volatile uint8_t *)scratch;
    bytes[0]=0x11; bytes[1]=0x22; bytes[2]=0x33; bytes[3]=0x44;
    if(scratch[0]!=0x44332211 || stack_test(10)!=23) fail(0xe3);
    /* First and last physical word of the otherwise unused SRAM. */
    *(volatile uint32_t *)0x10000000u=0x13579bdf;
    *(volatile uint32_t *)0x100000fcu=0x2468ace0;
    if(*(volatile uint32_t *)0x10000000u!=0x13579bdf ||
       *(volatile uint32_t *)0x100000fcu!=0x2468ace0) fail(0xe4);
    REG(7)=3;
    if(REG(0)!=5) fail(0xe5);
    REG(1)=9;
    if(REG(1)!=9) fail(0xe5);
    REG(7)=4;
    REG(3)='O'; while(REG(2)){}
    REG(3)='K'; while(REG(2)){}
    REG(7)=5;
    __asm__ volatile("csrw mtvec, %0" :: "r"(trap_entry));
    /* VexRiscv custom mask csr 0xbc0 selects external interrupt bit 0. */
    __asm__ volatile("csrw 0xbc0, %0" :: "r"(1));
    __asm__ volatile("csrs mie, %0" :: "r"(1u<<11));
    __asm__ volatile("csrs mstatus, %0" :: "r"(8));
    REG(4)=32;
    for(unsigned timeout=0;!irq_count;timeout++) if(timeout==10000) fail(0xe6);
    for(unsigned i=0;i<100;i++) __asm__ volatile("nop");
    if(irq_count!=1 || REG(5)) fail(0xe7);
    REG(7)=6;
    REG(6)=0x5a;
    for(;;){}
}
