// Passive observations at the slave pins, not a second bus master.
module bus_monitor #(
    parameter MEMORY = 0
)(input wire clk, rst, cyc, stb, ack, err, we,
  input wire [31:0] adr, dat_w, dat_r,
  input wire [3:0] sel, stage);
    reg waiting = 0;
    reg [31:0] saved_adr, saved_data;
    reg [3:0] saved_sel;
    reg saved_we;
    integer transfers = 0, waits = 0;
    always @(posedge clk) begin
        if (rst) waiting <= 0;
        else begin
            if (ack && err) $fatal(1, "BUS_PROTOCOL_ERROR ack_and_err");
            if (ack && !(cyc && stb)) $fatal(1, "BUS_PROTOCOL_ERROR unsolicited_ack");
            if (waiting && cyc && stb &&
                (adr != saved_adr || sel != saved_sel || we != saved_we || (we && dat_w != saved_data)))
                $fatal(1, "BUS_PROTOCOL_ERROR request_changed_while_waiting");
            waiting <= cyc && stb && !ack && !err;
            saved_adr <= adr; saved_data <= dat_w; saved_sel <= sel; saved_we <= we;
            if (cyc && stb && !ack && !err) waits <= waits + 1;
            if (cyc && stb && ack) begin
                transfers <= transfers + 1;
                if (MEMORY && stage == 7)
                    $display("MEMORY_TRANSACTION adr=0x%08x we=%0d sel=%x write=0x%08x read=0x%08x", adr, we, sel, dat_w, dat_r);
            end
        end
    end
    final $display("BUS_STATS memory=%0d transfers=%0d waits=%0d", MEMORY, transfers, waits);
endmodule
