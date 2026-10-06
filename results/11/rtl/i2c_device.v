// One 7-bit I2C device (0x42), two byte registers, open-drain SDA.
// The master provides the pull-up. This device only drives SDA low.
module i2c_device(
    input wire clk, rst, scl, sda,
    output reg release_sda
);
    localparam ADDR=0, REG=1, WRITE=2, READ=3, IGNORE=4,
               ACK_SETUP=5, ACK_HIGH=6, ACK_RELEASE=7,
               READ_ACK_SETUP=8, READ_ACK_HIGH=9, READ_ACK_RELEASE=10;
    reg [3:0] state, next_state;
    reg prev_scl, prev_sda;
    reg [2:0] bits;
    reg [7:0] shift, read_shift;
    reg [7:0] reg0, reg1;
    reg reg_index;
    reg ack_this;
    wire [7:0] incoming = {shift[6:0], sda};
    wire rising = scl && !prev_scl;
    wire falling = !scl && prev_scl;
    wire start_condition = scl && prev_scl && prev_sda && !sda;
    wire stop_condition = scl && prev_scl && !prev_sda && sda;

    always @(posedge clk) begin
        prev_scl <= scl;
        prev_sda <= sda;
        if (rst) begin
            state <= IGNORE;
            next_state <= IGNORE;
            release_sda <= 1;
            prev_scl <= 1;
            prev_sda <= 1;
            bits <= 0;
            shift <= 0;
            read_shift <= 0;
            reg0 <= 8'h12;
            reg1 <= 8'h34;
            reg_index <= 0;
            ack_this <= 0;
        end else if (start_condition) begin
            $display("I2C_START");
            state <= ADDR;
            bits <= 0;
            shift <= 0;
            release_sda <= 1;
        end else if (stop_condition) begin
            $display("I2C_STOP");
            state <= IGNORE;
            release_sda <= 1;
        end else begin
            case (state)
                ADDR, REG, WRITE: if (rising) begin
                    shift <= incoming;
                    bits <= bits + 1'b1;
                    if (bits == 7) begin
                        state <= ACK_SETUP;
                        bits <= 0;
                        if (state == ADDR) begin
                            ack_this <= incoming == 8'h84 || incoming == 8'h85;
                            next_state <= incoming == 8'h84 ? REG :
                                          incoming == 8'h85 ? READ : IGNORE;
                            $display("I2C_ADDRESS byte=0x%02x ack=%d", incoming,
                                     incoming == 8'h84 || incoming == 8'h85);
                        end else if (state == REG) begin
                            ack_this <= incoming < 2;
                            next_state <= incoming < 2 ? WRITE : IGNORE;
                            reg_index <= incoming[0];
                            $display("I2C_REGISTER index=%d ack=%d", incoming,
                                     incoming < 2);
                        end else begin
                            ack_this <= 1;
                            next_state <= IGNORE;
                            if (reg_index == 0) reg0 <= incoming;
                            else reg1 <= incoming;
                            $display("I2C_WRITE index=%d data=0x%02x", reg_index, incoming);
                        end
                    end
                end
                ACK_SETUP: if (falling) begin
                    release_sda <= !ack_this;
                    state <= ACK_HIGH;
                end
                ACK_HIGH: if (rising) state <= ACK_RELEASE;
                ACK_RELEASE: if (falling) begin
                    state <= next_state;
                    if (next_state == READ) begin
                        read_shift <= reg_index ? reg1 : reg0;
                        release_sda <= reg_index ? reg1[7] : reg0[7];
                        $display("I2C_READ index=%d data=0x%02x", reg_index,
                                 reg_index ? reg1 : reg0);
                    end else release_sda <= 1;
                end
                READ: begin
                    if (rising) begin
                        bits <= bits + 1'b1;
                        if (bits == 7) state <= READ_ACK_SETUP;
                    end
                    if (falling && bits != 0) begin
                        read_shift <= {read_shift[6:0], 1'b0};
                        release_sda <= read_shift[6];
                    end
                end
                READ_ACK_SETUP: if (falling) begin
                    release_sda <= 1;
                    state <= READ_ACK_HIGH;
                end
                READ_ACK_HIGH: if (rising) begin
                    $display("I2C_MASTER_NACK value=%d", sda);
                    state <= READ_ACK_RELEASE;
                end
                READ_ACK_RELEASE: if (falling) state <= IGNORE;
                default: ;
            endcase
        end
    end
endmodule
