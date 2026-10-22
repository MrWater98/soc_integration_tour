/* Local emulator for the actual dse_template MAC; upstream's template software
   stub still adds rs1+rs2, so it is not the reference for this experiment. */
#include <stdint.h>
static uint32_t accumulator;
static int signed_byte(uint32_t word,unsigned lane) {
    unsigned value=(word>>(lane*8))&255;
    return value<128 ? (int)value : (int)value-256;
}
uint32_t software_cfu(int funct3,int funct7,uint32_t a,uint32_t b) {
    (void)funct3;
    if(funct7) accumulator=0;
    else for(unsigned lane=0;lane<4;lane++)
        accumulator+=(uint32_t)((signed_byte(a,lane)+128)*signed_byte(b,lane));
    return accumulator;
}
