import json
import sys

data = {}
module = {}

# Supports abc gates:
# cmos2:  NAND NOR
# gates: AND NAND OR NOR XOR XNOR ANDNOT ORNOT
# aig:    AND NAND OR NOR ANDNOT ORNOT # And Inverter Graph
def get_fo4(_type, nin):
    if _type == "$_NOT_":
        if nin != 1:
            print("Error: NOT only has 1 input")
            exit(1)
        return 1
    if _type == "$_NAND_":
        if nin < 2 :
            print("Error: NAND gate have at least 2 inputs")
            exit(1)
        return (nin+2)/3
    if _type == "$_ANDNOT_":
        if nin < 2 :
            print("Error: ANDNOT gate have at least 2 inputs")
            exit(1)
        return (nin+2)/3
    if _type == "$_AND_":
        if nin < 2 :
            print("Error: AND gate have at least 2 inputs")
            exit(1)
        return 1+(nin+2)/3
    if _type == "$_NOR_":
        if nin < 2 :
            print("Error: NOR gate have at least 2 inputs")
            exit(1)
        return (2*nin+1)/3
    if _type == "$_OR_":
        if nin < 2 :
            print("Error: OR gate have at least 2 inputs")
            exit(1)
        return 1+(2*nin+1)/3
    if _type == "$_ORNOT_":
        if nin < 2 :
            print("Error: ORNOT gate have at least 2 inputs")
            exit(1)
        return (2*nin+1)/3
    if _type == "$_MUX_":
        if nin < 2 :
            print("Error: MUX gate have at least 2 inputs")
            exit(1)
        return 2
    if _type == "$_XOR_":
        if nin == 2:
            return 4;
        if nin == 3:
            return 12;
        if nin == 4:
            return 32;
        print("Error: Unknown FO4 for XOR with %d inputs" % nin)
        exit(1)
    if _type == "$_XNOR_":
        if nin == 2:
            return 4;
        if nin == 3:
            return 12;
        if nin == 4:
            return 32;
        print("Error: Unknown FO4 for XNOR with %d inputs" % nin)
        exit(1)
    print("Error: Unknown FO4 for gate: %s" % _type)
    exit(1)

if len(sys.argv) != 2:
    print("Error: mapping_to_fo4.py only expects 1 argument (the file to parse")
    exit(1)

print("tested: Yosys 0.9+4081 (git sha1 7a5ac909, clang 11.0.1-2 -fPIC -Os)")

def get_modules():
    return list(data["modules"].keys())

def get_cells():
        return module["cells"]

def get_cell(cellname):
        return get_cells()[cellname]

def get_cell_type(cellname):
        return get_cell(cellname)["type"]

def list_cell_outputs(cell):
    result = []
    for pin_name in cell["port_directions"]:
        if cell["port_directions"][pin_name] == 'output':
            for pin in cell["connections"][pin_name]:
                result.append(pin)
    return result

with open(sys.argv[1]) as json_file:
    data = json.load(json_file)
    # data is a 'dict' representation of the json
    # creator:
    # modules:
    #     <module' name>:
    #         attributes:
    #             cells_not_processed:
    #                 <string: number of not processed cells>
    #             src:
    #                 <string: filepath and version>
    #         ports:
    #             <port's name>:
    #                 direction:
    #                     <string: 'input'|'output'>
    #                 bits:
    #                     <array of integer>
    #         cells:
    #             <weird name>:
    #                 hide_name: <number>
    #                 type: <Ex: $_MUX_> # like in yosys's report
    #                 parameters: {}
    #                 attributes:
    #                     src: <string: path/version of techmap>
    #                 port_directions:
    #                     <port's name>: <string input|output>
    #                 connections:
    #                     <port's name>: <array of integers>
    #         netnames:
    #             <weird name>:
    #                 hide_name: <number>
    #                 bits: <array of integers>
    #                 attributes:
    #                     force_downto: <string: 0..01>
    #                     src: <path/version of techmap>
    module_list = get_modules()
    if len(module_list) > 1:
        print("Error: only single module are supported so far")
        exit(1)
    module_name = module_list[0]
    print(module_name)
    module = data["modules"][module_name]

    # Build a list which maps connections to cells with inputs connected to this connection
    connections = {} # order connections with they number (easier to navigate)
    # {42: [Cell_0, Cell_1, Cell_3], 23: ...}
    for cellname in get_cells():
        this_cell = get_cell(cellname)
        this_cell["name"] = cellname # for debug use later
        ctype = get_cell_type(cellname)
        num_inputs = 0
        for port in this_cell["port_directions"]:
            if this_cell["port_directions"][port] == "input":
                num_inputs += 1
                port_conn = this_cell["connections"][port]
                for pp in port_conn:
                    if not pp in connections:
                        connections[pp] = [this_cell]
                    else:
                        connections[pp].append(this_cell)

        this_cell["fo4"] = get_fo4(ctype, num_inputs)
        # we will propagate delays from the module's inputs to the outputs
        this_cell["max_prop_fo4"] = 0 # max
        this_cell["max_cell_count"] = 0
        this_cell["min_prop_fo4"] = 9999999999 # min
        this_cell["min_cell_count"] = 0

    # Iterate inputs and start propagating delays
    list_of_cells_to_propagate = []
    for port in module["ports"]:
        this_port = module["ports"][port]
        if this_port["direction"] == 'input':
            pins = this_port["bits"]
            for pin in pins:
                if not pin in connections:
                    print("Error: Module's input pin %d is not connected to any cell's input" % pin)
                    exit(1)
                for cell in connections[pin]:
                    list_of_cells_to_propagate.append(cell)
                    cell["max_prop_fo4"] = cell["fo4"]
                    cell["max_cell_count"] = 1
                    cell["min_prop_fo4"] = cell["fo4"]
                    cell["min_cell_count"] = 1

    # Propagate FO4
    overall_max_fo4 = 0
    overall_max_cell = 0
    max_cell = None
    overall_min_fo4 = 999999999999
    overall_min_cell = 0
    min_cell = None

    while len(list_of_cells_to_propagate)>0:
        new_list_of_cells_to_propagate = []
        for cell in list_of_cells_to_propagate:
            for cell_output in list_cell_outputs(cell):
                    if not cell_output in connections:
                        print("Info: %s output pin %d is not connected to any cell's input" % (cell["name"],cell_output))
                        if cell["max_prop_fo4"] > overall_max_fo4:
                            overall_max_fo4 = cell["max_prop_fo4"]
                            max_cell = cell
                            overall_max_cell = cell["max_cell_count"]
                        if cell["min_prop_fo4"] < overall_min_fo4:
                            overall_min_fo4 = cell["min_prop_fo4"]
                            min_cell = cell
                            overall_min_cell = cell["min_cell_count"]
                        continue
                    for target in connections[cell_output]:
                        new_list_of_cells_to_propagate.append(target)
                        if cell["max_prop_fo4"] + target["fo4"] > target["max_prop_fo4"]:
                            target["max_cell_count"] = cell["max_cell_count"] + 1
                            target["max_prop_fo4"] = cell["max_prop_fo4"] + target["fo4"]
                        if cell["min_prop_fo4"] + target["fo4"] < target["min_prop_fo4"]:
                            target["min_cell_count"] = cell["min_cell_count"] + 1
                            target["min_prop_fo4"] = cell["min_prop_fo4"] + target["fo4"]
        list_of_cells_to_propagate = new_list_of_cells_to_propagate
        print("Cells to propagate: {}".format(len(new_list_of_cells_to_propagate)))

    print("max FO4: {} - {} - ({})".format(overall_max_fo4, overall_max_cell, max_cell["name"]))
    print("min FO4: {} - {} - ({})".format(overall_min_fo4, overall_min_cell, min_cell["name"]))
