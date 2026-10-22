#include "Vasic_soc.h"
#include "verilated.h"
#include "verilated_cov.h"
#include <cstdio>
int main(int argc, char **argv) {
    Verilated::commandArgs(argc,argv);
    Vasic_soc soc;
    soc.sim_trace=0; soc.gpio_in=5; soc.reset_n=0;
    for(unsigned cycle=0;cycle<100000;cycle++) {
        if(cycle==4) soc.reset_n=1;
        soc.clk=0; soc.eval();
        soc.clk=1; soc.eval();
        if(soc.result) {
            VerilatedCov::write(argc>1 ? argv[1] : "coverage.dat");
            std::printf("COVERAGE_RUN cycles=%u result=%x\n",cycle,soc.result);
            return soc.result==0x5a ? 0:1;
        }
    }
    return 2;
}
