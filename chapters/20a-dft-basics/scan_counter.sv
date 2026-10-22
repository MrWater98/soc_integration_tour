// Small teaching counter. Only q[0] is visible during normal operation.
module scan_counter(input wire clk, reset, scan_enable, scan_in,
    input wire fault_enable, fault_value, input wire [1:0] fault_bit,
    output wire scan_out, normal_out);
    reg [3:0] q;
    wire [3:0] proposed = reset ? 4'b0 :
        scan_enable ? {q[2:0],scan_in} : q+4'd1;
    wire [3:0] mask = 4'b1 << fault_bit;
    wire [3:0] faulty = (proposed & ~mask) | (fault_value ? mask : 4'b0);
    always @(posedge clk)
        q <= fault_enable ? faulty : proposed;
    assign scan_out = q[3];
    assign normal_out = q[0];
endmodule
