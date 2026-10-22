#include <stdint.h>
#include <generated/csr.h>
#include <generated/soc.h>
#include "test_config.h"
static volatile uint32_t initialized = 0x12345678;
static volatile uint32_t zeroed;
static volatile uint32_t irq_count;
static volatile uint32_t ram[STRESS_WORDS];
static uint32_t rounds, state=TEST_SEED, last_irq;
static void character(char c) { while (uart_txfull_read()) {} uart_rxtx_write((uint8_t)c); }
static void text(const char *s) { while (*s) character(*s++); }
static void hex(uint32_t v) { for(int i=7;i>=0;i--) character("0123456789ABCDEF"[(v>>(4*i))&15]); }
static void fail(uint32_t code) { asm volatile("csrci mstatus, 8"); text("17 FAIL code=");hex(code);text("\r\n");for(;;){} }
void isr(void) {
 uint32_t cause;asm volatile("csrr %0, mcause":"=r"(cause));
 if (!(cause&0x80000000u) || !(timer0_ev_pending_read()&1u)) fail(1);
 timer0_ev_pending_write(1);irq_count++;
}
static uint32_t next(uint32_t x) {x^=x<<13;x^=x>>17;x^=x<<5;return x;}
static void pattern(uint32_t seed,int random) {
 uint32_t value=seed;
 for(uint32_t i=0;i<STRESS_WORDS;i++){if(random)value=next(value);ram[i]=random?value:seed;}
 if(INJECT_FAULT && rounds==3)ram[STRESS_WORDS/2]^=1;
 value=seed;
 for(uint32_t i=0;i<STRESS_WORDS;i++){if(random)value=next(value);if(ram[i]!=(random?value:seed))fail(0x10000000u|i);}
}
static void bytes(void) {
 ram[0]=0x11223344;
 volatile uint8_t *p=(volatile uint8_t *)&ram[0];
 p[0]=0x55;p[1]=0xaa;p[2]=0x66;p[3]=0xbb;
 if(ram[0]!=0xbb66aa55u)fail(2);
}
static void service(void) {
 static char command[64];static uint32_t used;
 while(!uart_rxempty_read()) {
  char c=(char)uart_rxtx_read();
  uart_ev_pending_write(2); /* RX event clear advances the default LiteX FIFO. */
  if(c=='\n') {
   command[used]=0;
   if(command[0]=='E'){text("17 ECHO ");text(command+1);text("\r\n");}
   if(command[0]=='R'){text("17 RESET\r\n");while(!uart_txempty_read()){}ctrl_reset_write(1);}
   used=0;
  } else if(c!='\r') {if(used<sizeof(command)-1)command[used++]=c;else fail(3);}
 }
}
int main(void) {
 if(initialized!=0x12345678u || zeroed || irq_count)fail(4);
 uart_ev_enable_write(0);
 text("17 BOOT hz=");hex(CONFIG_CLOCK_FREQUENCY);text(" seed=");hex(TEST_SEED);text("\r\n");
 timer0_en_write(0);timer0_ev_enable_write(0);timer0_load_write(0);
 timer0_reload_write(CONFIG_CLOCK_FREQUENCY/1000u);timer0_ev_pending_write(1);timer0_ev_enable_write(1);
 asm volatile("csrw 0xbc0, %0"::"r"(1u<<TIMER0_INTERRUPT));asm volatile("csrsi mstatus, 8");timer0_en_write(1);
 for(;;) {
  pattern(0,0);pattern(0xffffffffu,0);pattern(0xaaaaaaaau,0);pattern(0x55555555u,0);
  state=next(state);pattern(state,1);bytes();rounds++;service();
  leds_output_write(buttons_input_read()&1u);
  if(rounds%100u==0) {
   if(irq_count==last_irq)fail(5);last_irq=irq_count;
   text("17 PASS rounds=");hex(rounds);text(" irq=");hex(irq_count);text(" errors=00000000 reads=");hex(traffic_reads_read());text(" writes=");hex(traffic_writes_read());text("\r\n");
  }
 }
}
