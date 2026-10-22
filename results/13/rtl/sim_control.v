// Simulation-only controller. Runtime knobs never become architectural CSRs.
module sim_control #(
    parameter MAX_CYCLES = 2000000,
    parameter BIT_CYCLES = 10,
    parameter RESPONSE_WAIT = 8,
    parameter STRESS_BYTES = 128,
    parameter TIMER_PERIOD = 8000
)(
    input wire clk, sys_rst, tx, bus_wait, irq,
    input wire [3:0] stage,
    output reg test_reset = 0,
    output reg [31:0] fault = 0,
    output reg [31:0] workload_seed = 0,
    output reg [31:0] stress_count = STRESS_BYTES,
    output reg [31:0] timer_cycles = TIMER_PERIOD,
    output reg [31:0] bus_delay = RESPONSE_WAIT
);
    integer cycles = 0, reset_mode = 0, seed = 13, reset_delay = 0;
    integer state = 0, remaining = 0, reset_width = 8, reset_count = 1;
    integer resets = 0, reset_stage = 0;
    reg prev_tx = 1;
    initial begin
        if ($value$plusargs("fault=%d", fault)) begin end
        if ($value$plusargs("reset_mode=%d", reset_mode)) begin end
        if ($value$plusargs("seed=%d", seed)) begin end
        if ($value$plusargs("reset_delay=%d", reset_delay)) begin end
        if ($value$plusargs("reset_width=%d", reset_width)) begin end
        if ($value$plusargs("reset_count=%d", reset_count)) begin end
        if ($value$plusargs("reset_stage=%d", reset_stage)) begin end
        if ($value$plusargs("workload_seed=%d", workload_seed)) begin end
        if ($value$plusargs("stress_count=%d", stress_count)) begin end
        if ($value$plusargs("timer_cycles=%d", timer_cycles)) begin end
        if ($value$plusargs("bus_delay=%d", bus_delay)) begin end
        $display("SIM_CASE fault=%0d reset_mode=%0d seed=%0d delay=%0d workload_seed=%0d stress_count=%0d timer_cycles=%0d bus_delay=%0d reset_stage=%0d reset_count=%0d reset_width=%0d", fault, reset_mode, seed, reset_delay, workload_seed, stress_count, timer_cycles, bus_delay, reset_stage, reset_count, reset_width);
        if (bus_delay < 4 || bus_delay > 255 || reset_width < 2 || reset_count < 1 || reset_stage < 0 || reset_stage > 7 || reset_mode < 0 || reset_mode > 3 || stress_count < 1 || timer_cycles < 1000) $fatal(1, "invalid campaign parameters");
        if (reset_mode == 1 && (reset_delay < 1 || reset_delay >= 4*BIT_CYCLES)) $fatal(1, "invalid UART reset delay");
        if (reset_mode == 2 && (reset_delay < 0 || reset_delay >= bus_delay-2)) $fatal(1, "invalid bus reset delay");
    end
    always @(posedge clk) begin
        cycles <= cycles + 1;
        prev_tx <= tx;
        if (cycles >= MAX_CYCLES) $fatal(1, "SIM_TIMEOUT cycles=%0d", cycles);
        case (state)
            0: if (!sys_rst && stage >= reset_stage && ((reset_mode == 1 && prev_tx && !tx) ||
                               (reset_mode == 2 && bus_wait) ||
                               (reset_mode == 3 && irq))) begin
                state <= 1;
                remaining <= reset_delay;
                $display("RESET_TRIGGER mode=%0d seed=%0d cycle=%0d stage=%0d", reset_mode, seed, cycles, stage);
            end
            1: if (remaining == 0) begin
                test_reset <= 1;
                state <= 2;
                remaining <= reset_width-1;
                $display("RESET_ASSERT mode=%0d tx=%0d bus_wait=%0d irq=%0d cycle=%0d stage=%0d", reset_mode, tx, bus_wait, irq, cycles, stage);
            end else remaining <= remaining - 1;
            2: if (remaining == 0) begin
                test_reset <= 0;
                resets <= resets + 1;
                state <= 3;
                $display("RESET_RELEASE mode=%0d cycle=%0d", reset_mode, cycles);
            end else remaining <= remaining - 1;
            3: if (!sys_rst && resets < reset_count) state <= 0;
            default: ;
        endcase
    end
    final $display("SIM_CYCLES count=%0d resets=%0d", cycles, resets);
endmodule
