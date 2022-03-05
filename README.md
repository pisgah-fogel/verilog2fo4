# verilog2fo4
Verilog to FO4 - verilog2FO4 - Verilog to locical effort - yosys to fo4 - yosys to logical effort

FO4 is a process technology independent delay metric used in digital CMOS
technologies.

We assume P/N ratio is 2.

## Usage

## FO4 to frequency

|------|-----------|------------|------------------------------------------------------------------------|
| FO4  | Frequency | Technology | Source                                                                 |
|------|-----------|------------|------------------------------------------------------------------------|
| 13.0 | > 4.0 GHz | 65nm SOI   | <http://www.cs.wm.edu/~kemper/cs654/slides/power6.pdf>                 |
| 16.3 | 3.4 GHz   | 130nm      | <http://www.itrs.net/Links/2003ITRS/LinkedFiles/Design/FO4Writeup.pdf> |
| 12.4 | 6.0 GHZ?  | 90nm       | <http://www.itrs.net/Links/2003ITRS/LinkedFiles/Design/FO4Writeup.pdf> |


## How does it work?

```
# Calling:
VLOG_FILE_NAME=.../dut.v yosys get_mapping.tcl
# Will generate a json representation of the mapping
# it will be parsed by  mapping_to_fo4.py to get the fo4
python3 mapping_to_fo4.py mapping.json
```

```
yosys
read_verilog examples/nand_1.v
show # gui
synth # default synthesis
show # gui
```

```
# Synthethise to verilog builtin primitive:
yosys
read_verilog examples/nand_1.v
synth # default synthesis
abc -g AND,NAND,OR,NOR,XOR,XNOR # limit gates
clean
show # gui
wire_verilog net.v
```

```
# Map to a custom set of gates
read_verilog -lib cmos_cells_1.v
# translate processes to netlists, use multiplexers,
# flip-flips and latches
proc
# translate memory into basic cells, use DFFs and address decoders
# or multiport memory blocks (-nomap)
memory
techmap
clean
show # gui
```

## TODO

 - VHDL support

## Notes

From Power6 challenge example:
1 FO4 = delay of one inverter driving 4 receivers
1 Logical Gate = 2 FO4
1 cycle = Latch + function + wire = 3 FO4 + function + 4 FO4 = 3 + 3 + 4 = 10FO4
Function = 6 FO4 = 3 Gates
-> It takes 6 cycles to senf a signals across the core
-> Communication between units takes 1 cycle using good wire
-> Control across a 64-bit data flow takes a cycle

To learn more about FO4: <https://en.wikipedia.org/wiki/FO4>

Example of yosys cmos mapping: <https://github.com/YosysHQ/yosys/tree/master/examples/cmos>
