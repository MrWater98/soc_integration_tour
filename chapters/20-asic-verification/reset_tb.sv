`timescale 1ns/1ps
module tb;
    reg clk=0,reset_n=1;
    wire reset;
    integer i;
    reset_sync dut(.*);
    always #5 clk=~clk;
    task release_check;
        begin
            // Release away from the active edge, then inspect both stages.
            @(negedge clk); #2; reset_n=1;
            @(posedge clk); #1; if(reset!==1) $fatal(1,"Released before 2 clocks");
            @(posedge clk); #1; if(reset!==0) $fatal(1,"Did not release on 2nd clock");
        end
    endtask
    initial begin
        #1;reset_n=0;
        #1; if(reset!==1) $fatal(1,"Reset not asserted");
        release_check;
        for(i=0;i<8;i=i+1) begin
            // Different phase offsets, always long enough to be recognized.
            @(negedge clk); #(i%4+1);reset_n=0;
            #1;if(reset!==1) $fatal(1,"Async assertion failed");
            release_check;
        end
        $display("PASS_RESET assertions=9 releases=9");$finish;
    end
endmodule
