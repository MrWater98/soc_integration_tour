`timescale 1ns/1ps
module tb;
    reg clk=0, reset_n=0;
    reg [3:0] gpio_in=5;
    wire [3:0] gpio_out;
    wire uart_tx;
    wire [31:0] result;
    wire [7:0] stage;
    integer i;
    integer cycles=0, boots=0, serial_bytes=0, reset_stage=0;
    reg [7:0] received;
    reg resetting=0;
    asic_soc dut(.sim_trace(1'b0), .*);
    always #5 clk=~clk;
    initial begin
        if($value$plusargs("RESET_STAGE=%d",reset_stage)) begin end
        #13; reset_n=1;
    end
    // Independent receiver samples the physical TX pin at bit centers (8N1).
    initial forever begin
        @(negedge uart_tx);
        #(8*10+4*10);
        for(i=0;i<8;i=i+1) begin
            received[i]=uart_tx;
            #(8*10);
        end
        if(!uart_tx) $fatal(1,"UART stop bit invalid");
        $display("UART_BYTE value=%02x",received);
        if(serial_bytes%2==0 && received!==8'h4f) $fatal(1,"Expected O");
        if(serial_bytes%2==1 && received!==8'h4b) $fatal(1,"Expected K");
        serial_bytes=serial_bytes+1;
    end
    always @(negedge clk) begin
        cycles=cycles+1;
        if(cycles>100000) $fatal(1,"WATCHDOG stage=%d",stage);
        if(cycles>5 && reset_n && (^{uart_tx,gpio_out,result,stage} === 1'bx))
            $fatal(1,"Unknown external output");
        if(reset_stage!=0 && stage==reset_stage && !resetting) begin
            resetting=1;
            // Restart UART scoreboard; an interrupted frame is not a valid byte.
            // Campaign uses stages 2 and 5, outside active UART transmission.
            serial_bytes=0;
            reset_n=0;
            #23; reset_n=1;
            $display("RESET_INJECT stage=%0d",reset_stage);
        end
        if(result!=0) begin
            if(result!==32'h5a) $fatal(1,"FIRMWARE_FAIL result=%h stage=%d",result,stage);
            if(serial_bytes!=2 || gpio_out!=9 || stage!=6) $fatal(1,"Missing IO evidence");
            $display("PASS19 cycles=%0d UART=%0d GPIO=%h reset_injected=%0d",cycles,serial_bytes,gpio_out,resetting);
            $finish;
        end
    end
endmodule
