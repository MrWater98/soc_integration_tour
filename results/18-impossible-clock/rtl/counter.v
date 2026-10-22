// WIDTH is a design parameter; this pilot uses 16, not a PDK requirement.
module counter #(parameter WIDTH=16)(input clk, input reset, output reg [WIDTH-1:0] count);
always @(posedge clk) if (reset) count <= 0; else count <= count + 1'b1;
endmodule
