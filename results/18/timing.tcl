read_liberty /home/ziyue/researchlib/Micro_Eletronic/litex/soc_integration_tutorial/external/icsprout55-pdk/IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CR/liberty/ics55_LLSC_H7CR_typ_tt_1p2_25_nldm.lib
read_verilog /home/ziyue/researchlib/Micro_Eletronic/litex/soc_integration_tutorial/results/18/rtl/mapped.v
link_design counter
create_clock -name core -period 20 [get_ports clk]
set_input_delay 1 -clock core [get_ports reset]
set_output_delay 1 -clock core [get_ports count*]
report_checks -path_delay max -format full_clock_expanded
report_checks -path_delay min
exit
