`timescale 1ns/1ps
module tb;
    reg clk=0, reset=1, scan_enable=0, scan_in=0;
    reg fault_enable=0, fault_value=0;
    reg [1:0] fault_bit=0;
    wire scan_out,normal_out;
    integer fault=-1,mode=0,pattern,i,cycle=0,mismatches=0,file;
    reg expected;
    scan_counter dut(.*);
    task tick;
        begin #5; clk=1; #1; clk=0; #4; cycle=cycle+1; end
    endtask
    initial begin
        $dumpfile("scan.vcd");
        $dumpvars(0,tb);
        if($value$plusargs("FAULT=%d",fault)) begin end
        if($value$plusargs("MODE=%d",mode)) begin end
        file=$fopen("scan.csv","w");
        $fdisplay(file,"cycle,pattern,phase,scan_enable,scan_in,scan_out,expected,normal_out");
        if(fault>=0) begin
            fault_enable=1; fault_bit=fault/2; fault_value=fault%2;
        end
        tick; reset=0;
        if(mode==0) begin
            for(i=1;i<=16;i=i+1) begin
                tick;
                expected=i%2;
                if(normal_out!==expected) mismatches=mismatches+1;
                $fdisplay(file,"%0d,-,normal,0,0,%b,%b,%b",cycle,scan_out,expected,normal_out);
            end
        end else begin
            // Load MSB first: 4 shift edges leave q[3:0] equal to pattern.
            for(pattern=0;pattern<16;pattern=pattern+1) begin
                scan_enable=1;
                for(i=3;i>=0;i=i-1) begin
                    scan_in=(pattern>>i)&1;
                    tick;
                    $fdisplay(file,"%0d,%0d,load,1,%b,%b,-,%b",cycle,pattern,scan_in,scan_out,normal_out);
                end
                // Observe before each shift edge: q[3] is the next outgoing bit.
                for(i=3;i>=0;i=i-1) begin
                    expected=(pattern>>i)&1;
                    if(scan_out!==expected) mismatches=mismatches+1;
                    $fdisplay(file,"%0d,%0d,unload,1,0,%b,%b,%b",cycle,pattern,scan_out,expected,normal_out);
                    scan_in=0; tick;
                end
                // Reload, execute one business cycle, then scan out the capture.
                for(i=3;i>=0;i=i-1) begin scan_in=(pattern>>i)&1; tick; end
                scan_enable=0; tick; scan_enable=1;
                for(i=3;i>=0;i=i-1) begin
                    expected=((pattern+1)&15)>>i&1;
                    if(scan_out!==expected) mismatches=mismatches+1;
                    $fdisplay(file,"%0d,%0d,capture_unload,1,0,%b,%b,%b",cycle,pattern,scan_out,expected,normal_out);
                    scan_in=0; tick;
                end
            end
        end
        // Exit test mode; remove injected defect only for this separate recovery check.
        fault_enable=0; scan_enable=0; reset=1; tick; reset=0;
        for(i=1;i<=8;i=i+1) begin tick; if(normal_out!==(i%2!=0)) $fatal(1,"MODE_EXIT_FAIL"); end
        $fclose(file);
        $display("SCAN_RESULT fault=%0d mode=%0d mismatches=%0d recovery=PASS",fault,mode,mismatches);
        if(fault<0 && mismatches!=0) $fatal(1,"Healthy scan failed");
        $finish;
    end
endmodule
