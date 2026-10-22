// Bounded checks use arbitrary bus traffic, including unsupported byte strobes.
module properties(input wire clk);
    (* anyseq *) reg reset,cyc,stb,we;
    (* anyseq *) reg [3:0] sel,gpio_in;
    (* anyseq *) reg [29:0] adr;
    (* anyseq *) reg [31:0] dat_w;
    wire ack,uart_tx,irq;
    wire [31:0] dat_r,result;
    wire [3:0] gpio_out;
    wire [7:0] stage;
    peripheral dut(.*);
    reg past_valid=0;
    always @(posedge clk) begin
        past_valid <= 1;
        if(!past_valid) assume(reset);
        assert(!ack || (cyc && stb));
        if(past_valid) begin
            if($past(reset)) begin
                assert(result==0);
                assert(stage==0);
                assert(gpio_out==0);
                assert(!irq);
                assert(uart_tx);
            end else begin
                if($past(cyc && stb && ack && we && sel==15 && adr[3:0]==6))
                    assert(result==$past(dat_w));
                else assert(result==$past(result));
                if($past(cyc && stb && ack && we && sel==15 && adr[3:0]==5 && dat_w[0]))
                    assert(!irq);
            end
        end
    end
endmodule
