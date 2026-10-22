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
    always @* begin
        dat_r = 0;
        case(offset)
            0: dat_r = gpio_sync;
            1: dat_r = gpio_out;
            2: dat_r = {31'b0, tx_bits != 0};
            4: dat_r = timer_count;
            5: dat_r = timer_pending;
            6: dat_r = result;
            7: dat_r = stage;
        endcase
    end
    always @(posedge clk) begin
        if(reset) begin
            response_ready <= 0;
            gpio_meta <= 0; gpio_sync <= 0; gpio_out <= 0;
            timer_count <= 0; timer_enable <= 0; timer_pending <= 0;
            tx_shift <= 10'h3ff; tx_bits <= 0; tx_div <= 0;
            result <= 0; stage <= 0;
        end else begin
            response_ready <= request && !response_ready;
            gpio_meta <= gpio_in;
            gpio_sync <= gpio_meta;
            if(timer_enable) begin
                if(timer_count == 0) begin
                    timer_enable <= 0; timer_pending <= 1;
                end else timer_count <= timer_count - 1;
            end
            if(tx_bits != 0) begin
                if(tx_div == 0) begin
                    tx_shift <= {1'b1,tx_shift[9:1]};
                    tx_bits <= tx_bits - 1;
                    tx_div <= UART_DIV-1;
                end else tx_div <= tx_div - 1;
            end
            if(write) case(offset)
                1: gpio_out <= dat_w[GPIO_WIDTH-1:0];
                3: if(tx_bits == 0) begin
                    tx_shift <= {1'b1,dat_w[7:0],1'b0};
                    tx_bits <= 10; tx_div <= UART_DIV-1;
                end
                4: begin timer_count <= dat_w; timer_enable <= 1; end
                5: if(dat_w[0]) timer_pending <= 0;
                6: result <= dat_w;
                7: stage <= dat_w[7:0];
            endcase
        end
    end
endmodule
