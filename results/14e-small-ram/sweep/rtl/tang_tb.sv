`timescale 1ns/1ps
// Digital integration test only: ideal 27MHz simulation primitive replaces the hard PLL.
module tb;
  reg clk27=0,btn_n0=1,btn_n1=1;
  wire serial_tx,led4,led5;
  tutorial14 dut(.clk27(clk27),.btn_n0(btn_n0),.btn_n1(btn_n1),
    .serial_rx(1'b1),.serial_tx(serial_tx),.led4(led4),.led5(led5));
  always #18.518518 clk27=~clk27;
  integer count=0,hellos=0,ones=0,zeros=0,i;
  reg [7:0] value;
  string line="";
  initial begin
    forever begin
      @(negedge serial_tx);
      #(8680.555556/2);
      if(serial_tx!==0)$fatal(1,"UART start mismatch");
      for(i=0;i<8;i=i+1)begin
        #8680.555556;value[i]=serial_tx;
      end
      #8680.555556;
      if(serial_tx!==1)$fatal(1,"UART stop mismatch");
      if(value==10)begin
        $display("UART %s",line);
        if(line=="14 HELLO: CPU reached main; LEDs are mapped\r")hellos=hellos+1;
        if(line=="BUTTONS=0x00000001\r")ones=ones+1;
        if(line=="BUTTONS=0x00000000\r")zeros=zeros+1;
        line="";
      end else line={line,value};
    end
  end
  initial begin
    wait(hellos==1 && zeros==1);
    btn_n1=0;wait(ones==1);
    #10000;if(led5!==0)$fatal(1,"LED5 did not turn on");
    btn_n1=1;wait(zeros==2);
    #10000;if(led5!==1)$fatal(1,"LED5 did not turn off");
    btn_n0=0;repeat(10)@(posedge clk27);btn_n0=1;
    wait(hellos==2);
    $display("PASS TANG_DIGITAL_BOOT_BUTTON_RESET");$finish;
  end
  initial begin #50000000;$fatal(1,"digital simulation timeout");end
endmodule
