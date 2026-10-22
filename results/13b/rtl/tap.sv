// Teaching TAP: 16-state controller, IR, BYPASS, example ID and a user register.
// Teaching boundary cells, fixed four-bit board. Not a certified IEEE device.
module teaching_tap #(
    parameter integer IR_LEN = 4,
    parameter [31:0] EXAMPLE_IDCODE = 32'h12345679,
    parameter [31:0] USER_RESET = 32'hcafef00d
)(input wire tck, tms, tdi, trst_n, output reg tdo = 0,
  output reg [3:0] state = 0, output reg [IR_LEN-1:0] instruction = 2,
  output reg [31:0] user_data = USER_RESET,
  input wire [3:0] functional_out, pin_in, output wire [3:0] pin_out);
    reg [7:0] boundary_shift = 0;
    reg [3:0] boundary_drive = 0;
    // Teaching encodings: SAMPLE=4, EXTEST=5. Not device-independent opcodes.
    assign pin_out = instruction == 5 ? boundary_drive : functional_out;
    localparam RESET=0, IDLE=1, SELECT_DR=2, CAPTURE_DR=3, SHIFT_DR=4,
               EXIT1_DR=5, PAUSE_DR=6, EXIT2_DR=7, UPDATE_DR=8,
               SELECT_IR=9, CAPTURE_IR=10, SHIFT_IR=11, EXIT1_IR=12,
               PAUSE_IR=13, EXIT2_IR=14, UPDATE_IR=15;
    localparam [IR_LEN-1:0] ID_INSTRUCTION=2, USER_INSTRUCTION=3;
    reg [3:0] next_state = 0;
    reg [IR_LEN-1:0] ir_shift = 1;
    reg [31:0] dr_shift = 0;
    reg bypass = 0;
    always @* begin
        case(state)
            RESET: next_state = tms ? RESET : IDLE;
            IDLE: next_state = tms ? SELECT_DR : IDLE;
            SELECT_DR: next_state = tms ? SELECT_IR : CAPTURE_DR;
            CAPTURE_DR: next_state = tms ? EXIT1_DR : SHIFT_DR;
            SHIFT_DR: next_state = tms ? EXIT1_DR : SHIFT_DR;
            EXIT1_DR: next_state = tms ? UPDATE_DR : PAUSE_DR;
            PAUSE_DR: next_state = tms ? EXIT2_DR : PAUSE_DR;
            EXIT2_DR: next_state = tms ? UPDATE_DR : SHIFT_DR;
            UPDATE_DR: next_state = tms ? SELECT_DR : IDLE;
            SELECT_IR: next_state = tms ? RESET : CAPTURE_IR;
            CAPTURE_IR: next_state = tms ? EXIT1_IR : SHIFT_IR;
            SHIFT_IR: next_state = tms ? EXIT1_IR : SHIFT_IR;
            EXIT1_IR: next_state = tms ? UPDATE_IR : PAUSE_IR;
            PAUSE_IR: next_state = tms ? EXIT2_IR : PAUSE_IR;
            EXIT2_IR: next_state = tms ? UPDATE_IR : SHIFT_IR;
            UPDATE_IR: next_state = tms ? SELECT_DR : IDLE;
            default: next_state = RESET;
        endcase
    end
    always @(posedge tck or negedge trst_n) begin
        if (!trst_n) begin
            state <= RESET; instruction <= ID_INSTRUCTION;
            ir_shift <= 1; dr_shift <= 0; bypass <= 0; user_data <= USER_RESET;
            boundary_shift <= 0; boundary_drive <= 0;
        end else begin
            state <= next_state;
            if (next_state == RESET) instruction <= ID_INSTRUCTION;
            case(state)
                CAPTURE_IR: ir_shift <= 1; // low two capture bits are 01
                SHIFT_IR: ir_shift <= {tdi, ir_shift[IR_LEN-1:1]};
                UPDATE_IR: instruction <= ir_shift;
                CAPTURE_DR: begin
                    bypass <= 0;
                    boundary_shift <= {pin_out, pin_in};
                    if (instruction == ID_INSTRUCTION) dr_shift <= EXAMPLE_IDCODE;
                    else if (instruction == USER_INSTRUCTION) dr_shift <= user_data;
                end
                SHIFT_DR: begin
                    if (instruction == ID_INSTRUCTION || instruction == USER_INSTRUCTION)
                        dr_shift <= {tdi, dr_shift[31:1]};
                    else if (instruction == 4 || instruction == 5)
                        boundary_shift <= {tdi, boundary_shift[7:1]};
                    else bypass <= tdi;
                end
                UPDATE_DR: begin
                    if (instruction == USER_INSTRUCTION) user_data <= dr_shift;
                    if (instruction == 4 || instruction == 5) boundary_drive <= boundary_shift[7:4];
                end
                default: ;
            endcase
        end
    end
    // Drive the next serial bit on the falling edge; tester samples before rising.
    always @(negedge tck or negedge trst_n) begin
        if (!trst_n) tdo <= 0;
        else if (state == SHIFT_IR) tdo <= ir_shift[0];
        else if (state == SHIFT_DR && (instruction == 4 || instruction == 5))
            tdo <= boundary_shift[0];
        else if (state == SHIFT_DR)
            tdo <= (instruction == ID_INSTRUCTION || instruction == USER_INSTRUCTION) ? dr_shift[0] : bypass;
        else tdo <= 0;
    end
endmodule
