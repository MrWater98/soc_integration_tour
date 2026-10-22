`timescale 1ns/1ps
module tb;
    reg clk=0,reset=1,cyc=0,stb=0,we=0;
    reg [3:0] sel=0,gpio_in=5;
    reg [29:0] adr=0;
    reg [31:0] dat_w=0;
    wire ack,uart_tx,irq;
    wire [31:0] dat_r,result;
    wire [3:0] gpio_out;
    wire [7:0] stage;
    peripheral dut(.*);
    integer seed=1,count=10000,iteration,index,delay_cycles,k,aborts=0;
    reg [31:0] rng=1,model_result=0,expected;
    reg [3:0] model_gpio=0;
    reg [7:0] model_stage=0;
    integer coverage_hits[0:19];
    reg accepted=0;
    task advance_rng;
        begin rng=rng^(rng<<13);rng=rng^(rng>>17);rng=rng^(rng<<5);end
    endtask
    task tick;
        begin
            #5;clk=1;#1;
            if(reset) begin model_result=0;model_gpio=0;model_stage=0;end
            else if(cyc && stb && sel==15 && we) begin
                // ACK is sampled before the edge, stored by caller as accepted.
                if(accepted) case(adr[3:0])
                    1:model_gpio=dat_w[3:0];
                    6:model_result=dat_w;
                    7:model_stage=dat_w[7:0];
                endcase
            end
            if(result!==model_result || gpio_out!==model_gpio || stage!==model_stage)
                $fatal(1,"STRESS_SCOREBOARD i=%0d adr=%h",iteration,adr);
            clk=0;#4;
        end
    endtask
    initial begin
        for(k=0;k<20;k=k+1) coverage_hits[k]=0;
        if($value$plusargs("SEED=%d",seed)) begin end
        if($value$plusargs("COUNT=%d",count)) begin end
        rng=seed;
        tick;reset=0;tick;tick;
        for(iteration=0;iteration<count;iteration=iteration+1) begin
            advance_rng;index=rng%5;
            case(index) 0:adr=0;1:adr=1;2:adr=6;3:adr=7;4:adr=8;endcase
            advance_rng;we=rng[0];sel=rng[1]?15:1;
            advance_rng;dat_w=rng;
            advance_rng;delay_cycles=rng%6;
            cyc=0;stb=0;accepted=0;
            repeat(delay_cycles) tick;
            cyc=1;stb=1;#1;
            if(iteration%113==0) begin
                // Abort with reset before the first accepting clock edge.
                reset=1;accepted=0;tick;cyc=0;stb=0;reset=0;tick;tick;
                aborts=aborts+1;
            end else begin
                while(!ack) begin accepted=0;tick;end
                if(!we) begin
                    case(adr[3:0])
                        0:expected=5;
                        1:expected=model_gpio;
                        6:expected=model_result;
                        7:expected=model_stage;
                        default:expected=0;
                    endcase
                    if(dat_r!==expected) $fatal(1,"STRESS_READ i=%d got=%h expected=%h",iteration,dat_r,expected);
                end
                coverage_hits[index*4+we*2+(sel==15)]=coverage_hits[index*4+we*2+(sel==15)]+1;
                accepted=1;tick;accepted=0;cyc=0;stb=0;tick;
            end
        end
        for(k=0;k<20;k=k+1) begin
            $display("COVER_BIN id=%0d hits=%0d",k,coverage_hits[k]);
            if(coverage_hits[k]==0) $fatal(1,"Missing functional coverage bin %0d",k);
        end
        $display("PASS_STRESS seed=%0d requests=%0d reset_aborts=%0d coverage_hits=20/20",seed,count,aborts);
        $finish;
    end
endmodule
