`timescale 1ns/1ps
module tb;
    parameter DEPTH=8,WIDTH=8;
    localparam AW=$clog2(DEPTH);
    reg clk=0,we=0;
    reg [AW-1:0] address;
    reg [WIDTH-1:0] data_in;
    wire [WIDTH-1:0] data_out;
    reg [1:0] fault_kind=0;
    reg [7:0] fault_bit=0;
    reg fault_value=0;
    integer kind=0,bit_id=0,value=0,i,phase,step=0,mismatches=0,file;
    ram_model #(.DEPTH(DEPTH),.WIDTH(WIDTH)) dut(.*);
    task access(input integer addr,input integer writing,input [WIDTH-1:0] data);
        begin
            clk=0;address=addr;we=writing;data_in=data;
            #5;clk=1;#1;
            if(!writing && data_out!==data) mismatches=mismatches+1;
            $fdisplay(file,"%0d,%0d,%0d,%s,%h,%h",step,phase,addr,writing?"write":"read",data,data_out);
            #4;clk=0;step=step+1;
        end
    endtask
    initial begin
        if($value$plusargs("KIND=%d",kind)) begin end
        if($value$plusargs("BIT=%d",bit_id)) begin end
        if($value$plusargs("VALUE=%d",value)) begin end
        fault_kind=kind;fault_bit=bit_id;fault_value=value;
        file=$fopen("march.csv","w");
        $fdisplay(file,"step,phase,address,operation,expected_or_written,read_value");
        // March C-: ↑w0; ↑(r0,w1); ↑(r1,w0); ↓(r0,w1); ↓(r1,w0); ↑r0.
        phase=0;for(i=0;i<DEPTH;i=i+1) access(i,1,0);
        phase=1;for(i=0;i<DEPTH;i=i+1) begin access(i,0,0);access(i,1,{WIDTH{1'b1}});end
        phase=2;for(i=0;i<DEPTH;i=i+1) begin access(i,0,{WIDTH{1'b1}});access(i,1,0);end
        phase=3;for(i=DEPTH-1;i>=0;i=i-1) begin access(i,0,0);access(i,1,{WIDTH{1'b1}});end
        phase=4;for(i=DEPTH-1;i>=0;i=i-1) begin access(i,0,{WIDTH{1'b1}});access(i,1,0);end
        phase=5;for(i=0;i<DEPTH;i=i+1) access(i,0,0);
        $fclose(file);
        $display("RAM_RESULT kind=%0d bit=%0d value=%0d steps=%0d mismatches=%0d",kind,bit_id,value,step,mismatches);
        if(step!=10*DEPTH) $fatal(1,"Wrong March length");
        if(kind==0 && mismatches!=0) $fatal(1,"Healthy RAM failed");
        $finish;
    end
endmodule
