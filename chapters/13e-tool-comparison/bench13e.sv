`timescale 1ns/1ps
module bench13e;
    reg sys_clk = 0;
    wire sim_trace;
    always #5 sys_clk = ~sys_clk;
    sim dut(.sys_clk(sys_clk), .sim_trace(sim_trace));
    // The SoC ends the simulation on its completion write. This is a second
    // guard in case a different simulator does not honor its cycle watchdog.
    initial begin
        #25000000;
        $fatal(1, "BENCH13E_TIMEOUT");
    end
endmodule
