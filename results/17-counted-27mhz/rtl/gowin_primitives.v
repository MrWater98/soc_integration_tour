// Extracted unchanged modules from Yosys 0.60 techlibs/gowin/cells_sim.v.
// Yosys ISC license: https://github.com/YosysHQ/yosys/blob/main/COPYING
// rPLL is a primitive interface declaration, not a PLL behavioral model.

module DFFP (output reg Q, input D, CLK, PRESET);
  parameter [0:0] INIT = 1'b1;
  initial Q = INIT;

	specify
		(posedge CLK => (Q : D)) = (480, 660);
		(PRESET => Q) = (1800, 2679);
		$setup(D, posedge CLK, 576);
	endspecify

  always @(posedge CLK or posedge PRESET) begin
    if(PRESET)
      Q <= 1'b1;
    else
      Q <= D;
  end
endmodule

module DFFC (output reg Q, input D, CLK, CLEAR);
  parameter [0:0] INIT = 1'b0;
  initial Q = INIT;

	specify
		(posedge CLK => (Q : D)) = (480, 660);
		(CLEAR => Q) = (1800, 2679);
		$setup(D, posedge CLK, 576);
	endspecify

  always @(posedge CLK or posedge CLEAR) begin
    if(CLEAR)
      Q <= 1'b0;
    else
      Q <= D;
  end
endmodule

module rPLL (CLKOUT, CLKOUTP, CLKOUTD, CLKOUTD3, LOCK, CLKIN, CLKFB, FBDSEL, IDSEL, ODSEL, DUTYDA, PSDA, FDLY, RESET, RESET_P);
input CLKIN;
input CLKFB;
input RESET;
input RESET_P;
input [5:0] FBDSEL;
input [5:0] IDSEL;
input [5:0] ODSEL;
input [3:0] PSDA,FDLY;
input [3:0] DUTYDA;

output CLKOUT;
output LOCK;
output CLKOUTP;
output CLKOUTD;
output CLKOUTD3;

parameter FCLKIN = "100.0";         // frequency of CLKIN
parameter DYN_IDIV_SEL= "false";    // true:IDSEL, false:IDIV_SEL
parameter IDIV_SEL = 0;             // 0:1, 1:2 ... 63:64
parameter DYN_FBDIV_SEL= "false";   // true:FBDSEL, false:FBDIV_SEL
parameter FBDIV_SEL = 0;            // 0:1, 1:2 ... 63:64
parameter DYN_ODIV_SEL= "false";    // true:ODSEL, false:ODIV_SEL
parameter ODIV_SEL = 8;             // 2/4/8/16/32/48/64/80/96/112/128

parameter PSDA_SEL= "0000";
parameter DYN_DA_EN = "false";      // true:PSDA or DUTYDA or FDA, false: DA_SEL
parameter DUTYDA_SEL= "1000";

parameter CLKOUT_FT_DIR = 1'b1;     // CLKOUT fine tuning direction. 1'b1 only
parameter CLKOUTP_FT_DIR = 1'b1;    // 1'b1 only
parameter CLKOUT_DLY_STEP = 0;      // 0, 1, 2, 4
parameter CLKOUTP_DLY_STEP = 0;     // 0, 1, 2

parameter CLKFB_SEL = "internal";   // "internal", "external"
parameter CLKOUT_BYPASS = "false";  // "true", "false"
parameter CLKOUTP_BYPASS = "false"; // "true", "false"
parameter CLKOUTD_BYPASS = "false"; // "true", "false"
parameter DYN_SDIV_SEL = 2;         // 2~128, only even numbers
parameter CLKOUTD_SRC =  "CLKOUT";  // CLKOUT, CLKOUTP
parameter CLKOUTD3_SRC = "CLKOUT";  // CLKOUT, CLKOUTP
parameter DEVICE = "GW1N-1";        // "GW1N-1", "GW1N-4", "GW1N-9", "GW1NR-4", "GW1NR-9", "GW1N-4B", "GW1NR-4B", "GW1NS-2", "GW1NS-2C", "GW1NZ-1", "GW1NSR-2", "GW1NSR-2C", "GW1N-1S", "GW1NSE-2C", "GW1NRF-4B", "GW1N-9C", "GW1NR-9C", "GW1N-4C", "GW1NR-4C"

endmodule
