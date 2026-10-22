`timescale 1ns/1ps
// Real PDK IO-cell functional model experiment, not a completed pad ring.
module tb;
    supply1 vdd,vddio;
    supply0 vss,vssio;
    reg external_input=0, core_output=0, output_enable=0;
    wire input_to_core;
    wire input_pin=external_input;
    wire output_pad;
    P65_1233_PBMUX input_pad(.C(input_to_core),.A(),.PAD(input_pin),
        .IE(1'b1),.CS(1'b0),.I(1'b0),.OE(1'b0),.OD(1'b0),.PU(1'b0),.PD(1'b0),
        .DS0(1'b0),.DS1(1'b0),.VDD(vdd),.VDDIO(vddio),.VSS(vss),.VSSIO(vssio));
    P65_1233_PBMUX drive_pad(.C(),.A(),.PAD(output_pad),
        .IE(1'b0),.CS(1'b0),.I(core_output),.OE(output_enable),.OD(1'b0),.PU(1'b0),.PD(1'b0),
        .DS0(1'b0),.DS1(1'b0),.VDD(vdd),.VDDIO(vddio),.VSS(vss),.VSSIO(vssio));
    initial begin
        #1;if(input_to_core!==0) $fatal(1,"Input low failed");
        external_input=1;#1;if(input_to_core!==1) $fatal(1,"Input high failed");
        output_enable=1;#1;if(output_pad!==0) $fatal(1,"Output low failed");
        core_output=1;#1;if(output_pad!==1) $fatal(1,"Output high failed");
        output_enable=0;#1;if(output_pad!==1'bz) $fatal(1,"Output disable failed");
        $display("PASS_PAD input=0/1 output=0/1/Z");$finish;
    end
endmodule
