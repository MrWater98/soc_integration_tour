`timescale 1ns/1ps
module tb;
reg clk=0,reset=1; wire [15:0] count; integer expected=0,i;
counter dut(clk,reset,count);
always #10 clk=~clk;
initial begin
 for(i=0;i<70000;i=i+1) begin
  @(negedge clk);reset=(i<2 || i==33000);
  @(posedge clk); expected=reset?0:((expected+1)&65535);
  #1;if(count!==expected) $fatal(1,"counter mismatch cycle=%0d got=%h expected=%h",i,count,expected);
 end
 $display("PASS18 counter 70000 cycles, reset and wraparound");$finish;
end
endmodule
