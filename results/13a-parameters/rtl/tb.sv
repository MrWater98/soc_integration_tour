`timescale 1ns/1ps
module tb;
    reg tck=0, tms=1, tdi=0, trst_n=1;
    wire tdo;
    wire [3:0] state;
    wire [`IR_LENGTH-1:0] instruction;
    wire [31:0] user_data;
    teaching_tap #(.IR_LEN(`IR_LENGTH), .EXAMPLE_IDCODE(`IDCODE_VALUE)) dut(.*);
    integer fd, read_count, index=0, input_tms, input_tdi, expected_before, expected_after;
    integer bit_out;
    reg [4095:0] vector_file, wave_file;
    initial begin
        trst_n=0;
        if (!$value$plusargs("vectors=%s", vector_file)) $fatal(1,"missing vectors");
        if (!$value$plusargs("wave=%s", wave_file)) $fatal(1,"missing wave");
        $dumpfile(wave_file); $dumpvars(0,tb);
        #2; trst_n=1;
        fd=$fopen(vector_file,"r");
        if (!fd) $fatal(1,"cannot open vectors");
        while (!$feof(fd)) begin
            read_count=$fscanf(fd,"%d %d %d %d\n",input_tms,input_tdi,expected_before,expected_after);
            if (read_count != 4) $fatal(1,"invalid vector row");
            tms=input_tms; tdi=input_tdi;
            #5;
            if (state !== expected_before) $fatal(1,"wrong state before cycle %0d",index);
            bit_out=tdo;
            tck=1; #1;
            if (state !== expected_after) $fatal(1,"wrong transition cycle %0d",index);
            $display("TAP_CYCLE index=%0d pre=%0d tms=%0d tdi=%0d tdo=%0d post=%0d ir=%0d user=0x%08x",index,expected_before,tms,tdi,bit_out,state,instruction,user_data);
            #4; tck=0; #1;
            index=index+1;
        end
        $fclose(fd);
        $display("TAP_DONE cycles=%0d",index);
        $finish;
    end
    initial begin #200000; $fatal(1,"TAP_TIMEOUT"); end
endmodule
