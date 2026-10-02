// Read-only SPI Flash: command 0x03, 24-bit byte address, then streaming bytes.
module spi_flash_model(
    input wire clk, cs_n, sclk, mosi,
    output wire miso
);
    reg [7:0] mem [0:4095];
    reg old_clk, old_cs;
    reg [6:0] bit_count;
    reg [7:0] command;
    reg [23:0] address;
    reg [7:0] out_byte;
    wire rising = sclk && !old_clk;
    wire falling = !sclk && old_clk;
    assign miso = (!cs_n && bit_count >= 32 && command == 8'h03) ? out_byte[7] : 1'b1;
    initial $readmemh("flash_image.hex", mem);

    always @(posedge clk) begin
        old_clk <= sclk;
        old_cs <= cs_n;
        if (cs_n) begin
            if (!old_cs && bit_count == 64)
                $display("FLASH_READ command=0x%02x addr=0x%06x bits=%0d",
                         command, address, bit_count);
            bit_count <= 0;
            command <= 0;
            address <= 0;
            out_byte <= 8'hff;
        end else begin
            if (rising) begin
                bit_count <= bit_count + 1'b1;
                if (bit_count < 8) command <= {command[6:0], mosi};
                else if (bit_count < 32) begin
                    address <= {address[22:0], mosi};
                    if (bit_count == 31) out_byte <= mem[{address[22:0], mosi}];
                end
            end
            if (falling) begin
                if (bit_count >= 33 && bit_count <= 39) out_byte <= {out_byte[6:0], 1'b0};
                if (bit_count >= 41 && bit_count <= 47) out_byte <= {out_byte[6:0], 1'b0};
                if (bit_count >= 49 && bit_count <= 55) out_byte <= {out_byte[6:0], 1'b0};
                if (bit_count >= 57 && bit_count <= 63) out_byte <= {out_byte[6:0], 1'b0};
                if (bit_count == 40) out_byte <= mem[address + 1'b1];
                if (bit_count == 48) out_byte <= mem[address + 2'd2];
                if (bit_count == 56) out_byte <= mem[address + 2'd3];
            end
        end
    end
endmodule
