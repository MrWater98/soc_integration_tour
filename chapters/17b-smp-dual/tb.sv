`timescale 1ns/1ps
module tb;
 reg clk=0; always #500 clk=~clk;
 reg rst=1;
 wire tx;
 sim dut(.sys_clk(clk),.sys_rst(rst),.sim_trace(1'b0),.serial_rx(1'b1),.serial_tx(tx));
 integer boots=0;string line="";reg [7:0] byte_value;
 initial begin
  repeat(30) @(posedge clk);rst=0;
  #30000000000; $fatal(1,"SMP simulation timeout");
 end
 initial forever begin
  @(negedge tx); #15000;
  for(integer i=0;i<8;i=i+1)begin byte_value[i]=tx;#10000;end
  if(tx!==1'b1)$fatal(1,"UART stop bit");
  if(byte_value==10)begin
   $display("%s",line);
   if((__EXPECT_FAULT__ && line=="SMP FAIL __FAULT_MESSAGE__\r") || (!__EXPECT_FAULT__ && line=="SMP PASS harts=00000002\r"))begin
    boots=boots+1;
    if(boots==__REBOOTS__)begin $display("PASS SMP RESET_RUNS=%0d",boots);$finish;end
    rst=1;repeat(30)@(posedge clk);rst=0;
   end
   line="";
  end else line={line,byte_value};
 end
endmodule
