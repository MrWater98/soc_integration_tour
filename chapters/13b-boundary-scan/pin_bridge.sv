`timescale 1ns/1ps
// Simulator-side pin adapter. Commands are levels, not high-level register reads.
module pin_bridge;
 reg tck=0,tms=1,tdi=0,trst_n=0;
 wire tdo; wire [3:0] state,instruction; wire [31:0] user_data;
 reg [3:0] functional_out=4'ha;
 integer fault=0;
 wire [3:0] pin_out;
 wire [3:0] pin_in = fault==1 ? (pin_out & 4'hd) :
     fault==2 ? {pin_out[3:2],{2{pin_out[0]|pin_out[1]}}} : pin_out;
 teaching_tap dut(.tck(tck),.tms(tms),.tdi(tdi),.trst_n(trst_n),
 .tdo(tdo),.state(state),.instruction(instruction),.user_data(user_data),.functional_out(functional_out),.pin_in(pin_in),.pin_out(pin_out));
 integer count,ck,ms,di,rst,mode;
 reg [4095:0] wave;
 initial begin
  if ($value$plusargs("wave=%s",wave)) begin $dumpfile(wave); $dumpvars(0,pin_bridge); end
  #1;
  forever begin
   count=$fscanf(32'h80000000,"%d %d %d %d %d",ck,ms,di,rst,mode);
   if(count!=5) $finish;
   fault=mode;
   tms=ms;tdi=di;trst_n=rst; #1;tck=ck;#1;
   $display("PIN %0d %0d %0d %0d %0d %0d",tdo,state,instruction,user_data,pin_out,pin_in);
   $fflush();
  end
 end
endmodule
