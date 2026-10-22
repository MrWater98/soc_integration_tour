#include <stdint.h>
#include "cfu.h"
#define TRACE(n) (*(volatile uint32_t *)(0x80000000u+4u*(n)))

static const uint8_t inputs[8]={1,2,3,4,5,6,7,8};
static const int8_t weights[2][8]={{2,-1,3,1,-2,1,0,2},{-1,0,1,-2,1,1,-1,0}};
static const int32_t biases[2]={3,-2};
static volatile int32_t sink;

/* Ordinary scalar C, independent of the CFU state machine. */
__attribute__((noinline)) static int32_t reference_dot(const volatile uint8_t *x,const volatile int8_t *w,unsigned n) {
    int32_t sum=0;
    for(unsigned i=0;i<n;i++) sum+=(int32_t)x[i]*(int32_t)w[i];
    return sum;
}

/* The official CFU expects signed input bytes with a fixed +128 correction.
   Pack the first array element into bits7:0; do not depend on pointer casts. */
static uint32_t pack_inputs(const uint8_t *x,unsigned n) {
    uint32_t word=0;
    for(unsigned lane=0;lane<4;lane++) {
        int value=lane<n ? x[lane] : 0;
        word|=(uint32_t)(uint8_t)(value-128)<<(8*lane);
    }
    return word;
}
static uint32_t pack_weights(const int8_t *w,unsigned n) {
    uint32_t word=0;
    for(unsigned lane=0;lane<4;lane++)
        word|=(uint32_t)(lane<n ? (uint8_t)w[lane] : 0)<<(8*lane);
    return word;
}

__attribute__((noinline)) static int32_t accelerated_dot(const uint8_t *x,const int8_t *w,unsigned n) {
    cfu_op0(1,0,0); /* funct7=1 clears the persistent accumulator. */
    uint32_t result=0;
    for(unsigned i=0;i<n;i+=4) {
        unsigned remaining=n-i;
        if(remaining>4) remaining=4;
        result=cfu_op0(0,pack_inputs(x+i,remaining),pack_weights(w+i,remaining));
    }
    return (int32_t)result;
}
static uint32_t cycles(void) {
    uint32_t value;
    __asm__ volatile("rdcycle %0" : "=r"(value) :: "memory");
    return value;
}
static void fail(unsigned code) {TRACE(7)=code;for(;;){}}
static uint32_t random_state=0x12345678;
static uint32_t random_word(void) {
    random_state^=random_state<<13;
    random_state^=random_state>>17;
    random_state^=random_state<<5;
    return random_state;
}

int main(void) {
    /* One neuron without bias/activation: 1*2+2*(-1)+3*3+4*1=13. */
    int32_t dot=accelerated_dot(inputs,weights[0],4);
    if(dot!=13 || dot!=reference_dot(inputs,weights[0],4)) fail(0xe1);
    TRACE(1)=dot;
    for(unsigned output=0;output<2;output++) {
        int32_t sum=accelerated_dot(inputs,weights[output],8)+biases[output];
        int32_t ref=reference_dot(inputs,weights[output],8)+biases[output];
        int32_t activated=sum>0 ? sum:0;
        if(activated!=(ref>0 ? ref:0)) fail(0xe2);
        if(output==0 && activated!=28) fail(0xe2);
        if(output==1 && activated!=0) fail(0xe2);
        TRACE(2+output)=activated;
    }
    uint8_t x[17];int8_t w[17];
    for(unsigned test=0;test<64;test++) {
        unsigned n=1+test%17;
        for(unsigned i=0;i<n;i++) {x[i]=random_word();w[i]=(int8_t)random_word();}
        if(accelerated_dot(x,w,n)!=reference_dot(x,w,n)) fail(0xe3);
    }
    TRACE(6)=64;
    uint32_t start=cycles();
    for(unsigned i=0;i<64;i++) sink=reference_dot(inputs,weights[0],8);
    uint32_t scalar_cycles=cycles()-start;
    start=cycles();
    for(unsigned i=0;i<64;i++) sink=accelerated_dot(inputs,weights[0],8);
    uint32_t cfu_cycles=cycles()-start;
    uint32_t a0=pack_inputs(inputs,4),a1=pack_inputs(inputs+4,4);
    uint32_t b0=pack_weights(weights[0],4),b1=pack_weights(weights[0]+4,4);
    /* Make packing finish before the timed region; the asm emits no instruction. */
    __asm__ volatile("" : "+r"(a0), "+r"(b0), "+r"(a1), "+r"(b1) :: "memory");
    start=cycles();
    for(unsigned i=0;i<64;i++) {
        cfu_op0(1,0,0);
        cfu_op0(0,a0,b0);
        sink=(int32_t)cfu_op0(0,a1,b1);
    }
    uint32_t packed_cycles=cycles()-start;
    TRACE(4)=scalar_cycles;TRACE(5)=cfu_cycles;TRACE(8)=packed_cycles;
    if(sink!=25) fail(0xe4);
    TRACE(7)=0x5a;
    for(;;){}
}
