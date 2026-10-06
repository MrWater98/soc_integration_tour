/* Machine-generated using Migen */
module wishbone_register_slave(
	input [29:0] adr,
	input [31:0] dat_w,
	output [31:0] dat_r,
	input [3:0] sel,
	input cyc,
	input stb,
	output ack,
	input we,
	output err,
	output reg [31:0] registerslave,
	input sys_clk,
	input sys_rst
);

reg [1:0] registerslave1 = 2'd0;
reg [3:0] registerslave2 = 4'd0;
reg registerslave3 = 1'd0;
reg [31:0] registerslave4 = 32'd0;
reg [3:0] registerslave5 = 4'd0;

// synthesis translate_off
reg dummy_s;
initial dummy_s <= 1'd0;
// synthesis translate_on

assign ack = ((registerslave1 == 2'd2) | (registerslave1 == 2'd3));
assign dat_r = registerslave;
assign err = 1'd0;

always @(posedge sys_clk) begin
	if ((registerslave1 == 1'd0)) begin
		if (((cyc & stb) & (adr == 11'd1024))) begin
			registerslave3 <= we;
			registerslave4 <= dat_w;
			registerslave5 <= sel;
			registerslave2 <= 1'd0;
			registerslave1 <= 1'd1;
		end
	end else begin
		if ((registerslave1 == 1'd1)) begin
			if ((~(cyc & stb))) begin
				registerslave1 <= 1'd0;
			end else begin
				if ((registerslave2 != 1'd0)) begin
					registerslave2 <= (registerslave2 - 1'd1);
				end else begin
					if (1'd1) begin
						registerslave1 <= 2'd2;
					end
				end
			end
		end else begin
			if ((registerslave1 == 2'd2)) begin
				if (((cyc & stb) & registerslave3)) begin
					registerslave <= ((registerslave & (~{{8{registerslave5[3]}}, {8{registerslave5[2]}}, {8{registerslave5[1]}}, {8{registerslave5[0]}}})) | (registerslave4 & {{8{registerslave5[3]}}, {8{registerslave5[2]}}, {8{registerslave5[1]}}, {8{registerslave5[0]}}}));
				end
				registerslave1 <= 2'd3;
			end else begin
				if ((registerslave1 == 2'd3)) begin
					if ((~(cyc & stb))) begin
						registerslave1 <= 1'd0;
					end
				end
			end
		end
	end
	if (sys_rst) begin
		registerslave <= 32'd287454020;
		registerslave1 <= 2'd0;
		registerslave2 <= 4'd0;
		registerslave3 <= 1'd0;
		registerslave4 <= 32'd0;
		registerslave5 <= 4'd0;
	end
end

endmodule

