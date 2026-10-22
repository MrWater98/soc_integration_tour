create_clock -name core -period 20 [get_ports clk]
set_input_delay 1 -clock core [get_ports reset]
set_output_delay 1 -clock core [get_ports count*]
