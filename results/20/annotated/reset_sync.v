//      // verilator_coverage annotation
        // External reset asserts immediately; release takes two clock edges.
~008681 module reset_sync(input wire clk, input wire reset_n, output wire reset);
%000001     (* async_reg = "true" *) reg [1:0] release_pipe;
 004341     always @(posedge clk or negedge reset_n)
~004337         if (!reset_n) release_pipe <= 2'b00;
 004337         else release_pipe <= {release_pipe[0], 1'b1};
            assign reset = ~release_pipe[1];
        endmodule
        
