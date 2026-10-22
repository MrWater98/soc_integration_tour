#include <stdint.h>
#include <generated/csr.h>
#include "test_config.h"
#define MAIL ((volatile uint32_t *)0x40000100u)
static void fence(void){asm volatile("fence rw,rw" ::: "memory");}
static void text(const char*s){while(*s){while(uart_txfull_read()){}uart_rxtx_write(*s++);}}
static void hex(uint32_t x){for(int i=7;i>=0;i--){while(uart_txfull_read()){}uart_rxtx_write("0123456789ABCDEF"[(x>>(4*i))&15]);}}
void isr(void){
 uint32_t h,c;asm volatile("csrr %0,mhartid":"=r"(h));asm volatile("csrr %0,mcause":"=r"(c));
 if(c==0x80000007u){
  volatile uint32_t *cmp=(volatile uint32_t *)(0xf0014000u+8*h);
  cmp[0]=0xffffffffu;cmp[1]=0xffffffffu;
  ((volatile uint32_t *)0x400000d0u)[h]++;return;
 }
 if(c!=0x80000003u)for(;;){}
 *(volatile uint32_t *)(0xf0010000u+4*h)=0;
 ((volatile uint32_t *)0x400000c0u)[h]++;
}
int main(uint32_t hart){
 if(hart>=CPU_COUNT)for(;;){}
 if(hart==0){
  for(uint32_t h=0;h<CPU_COUNT;h++)for(uint32_t i=0;i<16;i++)MAIL[h*16+i]=0;
  *(volatile uint32_t *)0x40000040u=0;
  for(uint32_t h=0;h<CPU_COUNT;h++){((volatile uint32_t *)0x400000c0u)[h]=0;((volatile uint32_t *)0x400000d0u)[h]=0;}
  fence();
  for(uint32_t h=1;h<CPU_COUNT;h++)*(volatile uint32_t *)(0xf0010000u+4*h)=1;
 }else{
  while(!*(volatile uint32_t *)(0xf0010000u+4*hart)){}
  *(volatile uint32_t *)(0xf0010000u+4*hart)=0;fence();
 }
 if(FAULT_STOP && hart==CPU_COUNT-1)for(;;){}
 volatile uint32_t *slot=MAIL+hart*16; /* 64-byte separation: one cache line per mailbox. */
 /* Exercise the CLINT software interrupt path independently on each hart. */
 asm volatile("csrsi mie,8");asm volatile("csrsi mstatus,8");
 uint32_t spin;
 for(uint32_t k=1;k<=3;k++){
  *(volatile uint32_t *)(0xf0010000u+4*hart)=1;
  spin=0;while(((volatile uint32_t *)0x400000c0u)[hart]!=k)if(++spin==200000u)for(;;){}
 }
 asm volatile("csrci mie,8");
 volatile uint32_t *mtime=(volatile uint32_t *)0xf001bff8u;
 uint32_t hi,lo,hi2;do{hi=mtime[1];lo=mtime[0];hi2=mtime[1];}while(hi!=hi2);
 uint64_t when=(((uint64_t)hi<<32)|lo)+2000;
 volatile uint32_t *cmp=(volatile uint32_t *)(0xf0014000u+8*hart);
 cmp[0]=0xffffffffu;cmp[1]=(uint32_t)(when>>32);cmp[0]=(uint32_t)when;
 asm volatile("li t0,128;csrs mie,t0" ::: "t0");
 spin=0;while(!((volatile uint32_t *)0x400000d0u)[hart])if(++spin==200000u)for(;;){}
 asm volatile("csrci mstatus,8");
 volatile uint32_t *scratch=(volatile uint32_t *)(0x40002000u+hart*4096u);
 for(uint32_t i=0;i<512;i++)scratch[i]=0x5a5a0000u^i^hart;
 for(uint32_t i=0;i<512;i++)if(scratch[i]!=(0x5a5a0000u^i^hart)){slot[3]=0xbad;for(;;){}}
 scratch[0]=0x11223344u;((volatile uint8_t *)scratch)[1]=0xaau;
 if(scratch[0]!=0x1122aa44u){slot[3]=0xbad;for(;;){}}
 if(DELAY_HART && hart==CPU_COUNT-1)for(volatile uint32_t i=0;i<DELAY_HART;i++){}
 uint32_t sum=0;
 for(uint32_t i=1;i<=WORK;i++){sum+=i;slot[1]=i;
  uint32_t old;asm volatile("amoadd.w.aqrl %0,%2,(%1)":"=r"(old):"r"(0x40000040u),"r"(1u):"memory");}
 if(FAULT_MAILBOX)sum^=1;
 slot[0]=sum;slot[2]=hart;fence();slot[3]=0x600d0000u|hart;fence();
 if(hart)for(;;){}
 for(uint32_t spins=0;;spins++){
  uint32_t ready=1;for(uint32_t h=0;h<CPU_COUNT;h++)if(MAIL[h*16+3]!=(0x600d0000u|h))ready=0;
  fence();if(ready)break;
  if(spins==200000u){text("SMP FAIL timeout\r\n");for(;;){}}
 }
 for(uint32_t h=0;h<CPU_COUNT;h++){
  volatile uint32_t *m=MAIL+h*16;
  if(m[0] != WORK*(WORK+1u)/2u || m[1]!=WORK || m[2]!=h){text("SMP FAIL mailbox\r\n");for(;;){}}
  text("SMP HART ");hex(h);text(" count=");hex(m[1]);text(" sum=");hex(m[0]);text("\r\n");
 }
 if(*(volatile uint32_t *)0x40000040u!=WORK*CPU_COUNT){text("SMP FAIL atomic\r\n");for(;;){}}
 text("SMP ATOMIC count=");hex(*(volatile uint32_t *)0x40000040u);text("\r\n");
 for(uint32_t h=0;h<CPU_COUNT;h++)if(((volatile uint32_t *)0x400000c0u)[h]!=3){text("SMP FAIL irq\r\n");for(;;){}}
 text("SMP IRQ PASS\r\n");
 for(uint32_t h=0;h<CPU_COUNT;h++)if(((volatile uint32_t *)0x400000d0u)[h]!=1){text("SMP FAIL timer\r\n");for(;;){}}
 text("SMP TIMER PASS\r\n");
 text("SMP PASS harts=");hex(CPU_COUNT);text("\r\n");for(;;){}
}
