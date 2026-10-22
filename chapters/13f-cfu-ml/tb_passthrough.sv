`timescale 1ns/1ps
module tb;
    reg clk=0,reset=0,cmd_valid=0,rsp_ready=0;
    reg [9:0] cmd_payload_function_id=0;
    reg [31:0] cmd_payload_inputs_0=32'h12345678,cmd_payload_inputs_1=32'habcdef01;
    wire cmd_ready,rsp_valid;
    wire [31:0] rsp_payload_outputs_0;
    integer i;
    Cfu dut(.*);
    initial begin
        for(i=0;i<8;i=i+1) begin
            cmd_payload_function_id=i;cmd_valid=(i>>1)&1;rsp_ready=(i>>2)&1;
            #1;
            if(cmd_ready!==rsp_ready || rsp_valid!==cmd_valid) $fatal(1,"Passthrough handshake");
            if(rsp_payload_outputs_0!==(i&1 ? cmd_payload_inputs_1:cmd_payload_inputs_0))
                $fatal(1,"Passthrough data");
        end
        $display("PASS_PASSTHROUGH cases=8");$finish;
    end
endmodule
