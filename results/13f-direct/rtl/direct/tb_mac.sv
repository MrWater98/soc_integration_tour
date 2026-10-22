`timescale 1ns/1ps
module tb;
    reg clk=0,reset=1,cmd_valid=0,rsp_ready=0;
    wire cmd_ready,rsp_valid;
    reg [9:0] cmd_payload_function_id;
    reg [31:0] cmd_payload_inputs_0,cmd_payload_inputs_1;
    wire [31:0] rsp_payload_outputs_0;
    integer vectors,trace,count=0,rc,hold_cycles,i,cycle=0;
    reg [31:0] expected;
    reg accepted_cmd,accepted_rsp,ready_before,valid_before;
    reg [31:0] result_before;
    Cfu dut(.*);
    task tick;
        begin
            accepted_cmd=cmd_valid && cmd_ready;accepted_rsp=rsp_valid && rsp_ready;
            ready_before=cmd_ready;valid_before=rsp_valid;result_before=rsp_payload_outputs_0;
            #5;clk=1;#1;
            $fdisplay(trace,"%0d,%b,%b,%b,%b,%b,%b,%03h,%08h,%08h,%08h,%08h",cycle,accepted_cmd,accepted_rsp,cmd_valid,ready_before,valid_before,rsp_ready,cmd_payload_function_id,cmd_payload_inputs_0,cmd_payload_inputs_1,result_before,rsp_payload_outputs_0);
            clk=0;#4;cycle=cycle+1;
        end
    endtask
    initial begin
        trace=$fopen("cfu_cycles.csv","w");
        $fdisplay(trace,"cycle,accepted_cmd,accepted_rsp,cmd_valid_before,cmd_ready_before,rsp_valid_before,rsp_ready_before,function_id,input0,input1,result_before,result_after");
        $dumpfile("cfu.vcd");$dumpvars(0,tb);
        tick;reset=0;
        vectors=$fopen("vectors.txt","r");
        if(!vectors) $fatal(1,"Missing vectors.txt");
        while(!$feof(vectors)) begin
            rc=$fscanf(vectors,"%h %h %h %h %d\n",cmd_payload_function_id,cmd_payload_inputs_0,cmd_payload_inputs_1,expected,hold_cycles);
            if(rc!=5) $fatal(1,"Malformed vector");
            if(!cmd_ready) $fatal(1,"CFU unexpectedly busy");
            cmd_valid=1;tick;cmd_valid=0;
            if(!rsp_valid || rsp_payload_outputs_0!==expected)
                $fatal(1,"MAC_MISMATCH vector=%0d actual=%h expected=%h",count,rsp_payload_outputs_0,expected);
            for(i=0;i<hold_cycles;i=i+1) begin
                tick;
                if(!rsp_valid || cmd_ready || rsp_payload_outputs_0!==expected)
                    $fatal(1,"Response changed under backpressure");
            end
            rsp_ready=1;tick;rsp_ready=0;
            if(rsp_valid || !cmd_ready) $fatal(1,"Response not consumed");
            count=count+1;
        end
        // Reset with an outstanding response: discard it, clear accumulator.
        cmd_payload_function_id=0;cmd_payload_inputs_0=32'h84838281;
        cmd_payload_inputs_1=32'h0103ff02;cmd_valid=1;tick;cmd_valid=0;
        reset=1;tick;reset=0;
        if(rsp_valid || rsp_payload_outputs_0!==0) $fatal(1,"Reset failed");
        cmd_valid=1;tick;cmd_valid=0;
        if(!rsp_valid || rsp_payload_outputs_0!==13) $fatal(1,"Post-reset MAC failed");
        $fclose(trace);$fclose(vectors);
        $display("PASS_MAC vectors=%0d backpressure=0..7 reset_recovery=PASS",count);$finish;
    end
endmodule
