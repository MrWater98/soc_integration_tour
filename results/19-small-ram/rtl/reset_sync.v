// External reset asserts immediately; release takes two clock edges.
module reset_sync(input wire clk, input wire reset_n, output wire reset);
    (* async_reg = "true" *) reg [1:0] release_pipe;
    always @(posedge clk or negedge reset_n)
        if (!reset_n) release_pipe <= 2'b00;
        else release_pipe <= {release_pipe[0], 1'b1};
    assign reset = ~release_pipe[1];
endmodule
