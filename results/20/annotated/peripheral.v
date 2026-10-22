//      // verilator_coverage annotation
        // A small Wishbone register endpoint. Addresses here are word offsets.
        module peripheral #(parameter GPIO_WIDTH=4, UART_DIV=8)(
            input wire clk, reset,
            input wire cyc, stb, we, input wire [3:0] sel,
            input wire [29:0] adr, input wire [31:0] dat_w,
            output wire ack, output reg [31:0] dat_r,
            input wire [GPIO_WIDTH-1:0] gpio_in,
            output reg [GPIO_WIDTH-1:0] gpio_out,
            output wire uart_tx, output wire irq,
            output reg [31:0] result, output reg [7:0] stage);
            (* async_reg = "true" *) reg [GPIO_WIDTH-1:0] gpio_meta, gpio_sync;
            reg [31:0] timer_count;
            reg timer_enable, timer_pending;
            reg [9:0] tx_shift;
            reg [3:0] tx_bits;
            reg [15:0] tx_div;
            reg response_ready;
            wire request = cyc && stb;
            wire write = request && ack && we && sel == 4'hf;
            wire [3:0] offset = adr[3:0];
            assign ack = request && response_ready;
            assign irq = timer_pending;
            assign uart_tx = tx_bits != 0 ? tx_shift[0] : 1'b1;
 004342     always @* begin
 004342         dat_r = 0;
 004342         case(offset)
 000782             0: dat_r = gpio_sync;
 000320             1: dat_r = gpio_out;
 000300             2: dat_r = {31'b0, tx_bits != 0};
 000397             4: dat_r = timer_count;
 000294             5: dat_r = timer_pending;
 000273             6: dat_r = result;
 000308             7: dat_r = stage;
                endcase
            end
 004341     always @(posedge clk) begin
 004335         if(reset) begin
 000006             response_ready <= 0;
 000006             gpio_meta <= 0; gpio_sync <= 0; gpio_out <= 0;
 000006             timer_count <= 0; timer_enable <= 0; timer_pending <= 0;
 000006             tx_shift <= 10'h3ff; tx_bits <= 0; tx_div <= 0;
 000006             result <= 0; stage <= 0;
 004335         end else begin
 004335             response_ready <= request && !response_ready;
 004335             gpio_meta <= gpio_in;
 004335             gpio_sync <= gpio_meta;
 004302             if(timer_enable) begin
 000032                 if(timer_count == 0) begin
 000001                     timer_enable <= 0; timer_pending <= 1;
 000032                 end else timer_count <= timer_count - 1;
                    end
 004175             if(tx_bits != 0) begin
 000140                 if(tx_div == 0) begin
 000020                     tx_shift <= {1'b1,tx_shift[9:1]};
 000020                     tx_bits <= tx_bits - 1;
 000020                     tx_div <= UART_DIV-1;
 000140                 end else tx_div <= tx_div - 1;
                    end
 004323             if(write) case(offset)
 000001                 1: gpio_out <= dat_w[GPIO_WIDTH-1:0];
~000002                 3: if(tx_bits == 0) begin
 000002                     tx_shift <= {1'b1,dat_w[7:0],1'b0};
 000002                     tx_bits <= 10; tx_div <= UART_DIV-1;
                        end
 000001                 4: begin timer_count <= dat_w; timer_enable <= 1; end
~000001                 5: if(dat_w[0]) timer_pending <= 0;
 000001                 6: result <= dat_w;
 000006                 7: stage <= dat_w[7:0];
                    endcase
                end
            end
        endmodule
        
