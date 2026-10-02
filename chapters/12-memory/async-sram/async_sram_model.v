// Byte-wide asynchronous SRAM. Reads follow CE/OE/address; writes use WE-low.
module async_sram_model(
    input wire clk,
    input wire ce_n, oe_n, we_n,
    input wire [11:0] adr,
    inout wire [7:0] dat
);
    reg [7:0] mem [0:4095];
    integer i;
    initial for (i = 0; i < 4096; i = i + 1) mem[i] = 0;
    assign dat = (!ce_n && !oe_n && we_n) ? mem[adr] : 8'bz;
    always @(posedge clk) begin
        if (!ce_n && !we_n) begin
            mem[adr] <= dat;
            if (adr == 0 || adr == 4095)
                $display("ASRAM_PAD_WRITE byte=0x%03x data=0x%02x", adr, dat);
        end
    end
endmodule
