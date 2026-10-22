// Synchronous, single-port teaching RAM with explicit digital fault injection.
module ram_model #(parameter DEPTH=8, WIDTH=8, AW=$clog2(DEPTH))(
    input wire clk,we, input wire [AW-1:0] address,
    input wire [WIDTH-1:0] data_in, output reg [WIDTH-1:0] data_out,
    input wire [1:0] fault_kind, input wire [7:0] fault_bit,
    input wire fault_value);
    reg [WIDTH-1:0] memory[0:DEPTH-1];
    wire [AW-1:0] physical_address = fault_kind==2 ?
        address & ~(1 << fault_bit) : address;
    wire [WIDTH-1:0] mask = 1 << fault_bit;
    function [WIDTH-1:0] corrupt(input [WIDTH-1:0] value);
        corrupt = fault_kind==1 ? (value & ~mask) | (fault_value ? mask : 0) : value;
    endfunction
    always @(posedge clk) begin
        if(we) memory[physical_address] <= corrupt(data_in);
        data_out <= corrupt(memory[physical_address]);
    end
endmodule
