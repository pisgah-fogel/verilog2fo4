# Usage:
# VLOG_FILE_NAME=.../dut.v yosys get_mapping.tcl

yosys read_verilog $::env(VLOG_FILE_NAME)
#yosys read_verilog -lib cmos_cells_1.v
yosys proc
yosys memory
#yosys techmap -map cmos_cells_1.v
yosys synth
yosys abc -g AND,NAND,OR,NOR,ANDNOT,ORNOT # limit gates
yosys clean
yosys json -o mapping.json
yosys show
