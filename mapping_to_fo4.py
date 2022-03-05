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
        if nin < 2:
            print("Error: NAND gate have at least 2 inputs")
            exit(1)
        return (nin+2)/3
    if _type == "$_ANDNOT_":
        if nin < 2:
            print("Error: ANDNOT gate have at least 2 inputs")
            exit(1)
        return (nin+2)/3
    if _type == "$_AND_":
        if nin < 2:
            print("Error: AND gate have at least 2 inputs")
            exit(1)
        return 1+(nin+2)/3
    if _type == "$_NOR_":
        if nin < 2:
            print("Error: NOR gate have at least 2 inputs")
            exit(1)
        return (2*nin+1)/3
    if _type == "$_OR_":
        if nin < 2:
            print("Error: OR gate have at least 2 inputs")
            exit(1)
        return 1+(2*nin+1)/3
    if _type == "$_ORNOT_":
        if nin < 2:
            print("Error: ORNOT gate have at least 2 inputs")
            exit(1)
        return (2*nin+1)/3
    if _type == "$_MUX_":
        if nin < 2:
            print("Error: MUX gate have at least 2 inputs")
            exit(1)
        return 2
    if _type == "$_XOR_":
        if nin == 2:
            return 4
        if nin == 3:
            return 12
        if nin == 4:
            return 32
        print("Error: Unknown FO4 for XOR with %d inputs" % nin)
        exit(1)
    if _type == "$_XNOR_":
        if nin == 2:
            return 4
        if nin == 3:
            return 12
        if nin == 4:
            return 32
        print("Error: Unknown FO4 for XNOR with %d inputs" % nin)
        exit(1)
    print("Error: Unknown FO4 for gate: %s" % _type)
    exit(1)


if len(sys.argv) != 2:
    print("Error: mapping_to_fo4.py only expects 1 argument (the file to parse")
    exit(1)

print("Tested: Yosys 0.9+4081 (git sha1 7a5ac909, clang 11.0.1-2 -fPIC -Os)")


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

    def pin_pretty_name(pin_number):
        for netname in module["netnames"]:
            net = module["netnames"][netname]
            counter = 0
            if pin_number in net["bits"]:
                return "{}[{}] (net {})".format(netname, counter, pin_number)
                counter += 1
        print("Error: Cannot find net (aka connection) %d in the netnames".format(
            pin_number))

        # Build a list which maps connections to cells with inputs connected to this connection
        # order all connections with they number (easier to navigate)
    connections = {}
    # {42: [Cell_0, Cell_1, Cell_3], 23: ...}
    for cellname in get_cells():
        this_cell = get_cell(cellname)
        this_cell["name"] = cellname  # for debug use later
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
        this_cell["max_prop_fo4"] = 0  # max
        this_cell["max_cell_count"] = 0
        this_cell["min_prop_fo4"] = 9999999999  # min
        this_cell["min_cell_count"] = 0

    # Iterate inputs and start propagating delays
    list_of_cells_to_propagate = []
    this_module_output_pings = []
    for port in module["ports"]:
        this_port = module["ports"][port]
        if this_port["direction"] == 'input':
            pins = this_port["bits"]
            for pin in pins:
                if not pin in connections:
                    print(
                        "Warning: Module's input pin %s is not connected to any cell's input" % pin_pretty_name(pin))
                    continue
                for cell in connections[pin]:
                    if not cell in list_of_cells_to_propagate:
                        list_of_cells_to_propagate.append(cell)
                    cell["max_prop_fo4"] = cell["fo4"]
                    cell["max_cell_count"] = 1
                    cell["min_prop_fo4"] = cell["fo4"]
                    cell["min_cell_count"] = 1
        elif this_port["direction"] == 'output':
            pins = this_port["bits"]
            for pin in pins:
                this_module_output_pings.append(pin)

    def is_pin_output(pin_to_search):
        return pin_to_search in this_module_output_pings

        # Propagate FO4
    output_cells = []  # cells which outputs are not connected
    output_pin_max_fo4 = {}
    output_pin_min_fo4 = {}
    output_pin_max_cell = {}
    output_pin_min_cell = {}
    output_pin_last_cell = {}

    while len(list_of_cells_to_propagate) > 0:
        new_list_of_cells_to_propagate = []
        for cell in list_of_cells_to_propagate:  # For all cells which had an output propagated to them
            # For each output_pin of this cell
            for cell_output_pin in list_cell_outputs(cell):
                # Open output, cannot propagate further
                cell_output_pin_open = not cell_output_pin in connections
                cell_output_pin_is_output = is_pin_output(cell_output_pin)
                if cell_output_pin_open or cell_output_pin_is_output:
                    if cell_output_pin_is_output:
                        print("Done propagating to output pin {}, last cell was {}".format(
                            pin_pretty_name(cell_output_pin), cell['name']))
                    else:
                        print("Warning: %s is not connected to any other cell, last cell was %s" % (
                            pin_pretty_name(cell_output_pin), cell["name"]))

                    # error detection
                    if cell_output_pin in output_pin_max_fo4:
                        print(
                            "Error: We are already done processing output pin %s but you try to duplicate it's entry" % pin_pretty_name(cell_output_pin))
                    assert(not cell_output_pin in output_pin_max_fo4)

                    output_pin_max_fo4[cell_output_pin] = cell["max_prop_fo4"]
                    output_pin_min_fo4[cell_output_pin] = cell["min_prop_fo4"]
                    output_pin_max_cell[cell_output_pin] = cell["max_cell_count"]
                    output_pin_min_cell[cell_output_pin] = cell["min_cell_count"]
                    output_pin_last_cell[cell_output_pin] = cell
                    if not cell in output_cells:
                        output_cells.append(cell)

                    if cell_output_pin_open:
                        continue
                    else:
                        pass  # We need to propagate
                for target in connections[cell_output_pin]:
                    if not target in new_list_of_cells_to_propagate:
                        # only add cell once even if multiple inputs
                        new_list_of_cells_to_propagate.append(target)
                    if cell["max_prop_fo4"] + target["fo4"] > target["max_prop_fo4"]:
                        target["max_cell_count"] = cell["max_cell_count"] + 1
                        target["max_prop_fo4"] = cell["max_prop_fo4"] + \
                            target["fo4"]
                    if cell["min_prop_fo4"] + target["fo4"] < target["min_prop_fo4"]:
                        target["min_cell_count"] = cell["min_cell_count"] + 1
                        target["min_prop_fo4"] = cell["min_prop_fo4"] + \
                            target["fo4"]
        list_of_cells_to_propagate = new_list_of_cells_to_propagate
        # Debug
        # print("Cells to propagate: {}".format(
        #    len(new_list_of_cells_to_propagate)))

    print("List of output signals and Min/Max FO4")
    print("max FO4 | max chain | min F04 | min chain | name")
    for i in output_pin_last_cell:
        print("{: >3} | {:7.2f} | {: >9} | {:7.2f} | {: >9} | {} from cell {}".format(
            output_pin_max_fo4[i], output_pin_max_cell[i], output_pin_min_fo4[i],
            output_pin_min_cell[i], pin_pretty_name(i),
            output_pin_last_cell[i]["name"]
        ))

    print("\nFO4 Summary:")
    max_fo4 = 0
    max_fo4_index = 0
    for i in output_pin_max_fo4:
        if output_pin_max_fo4[i] > max_fo4:
            max_fo4 = output_pin_max_fo4[i]
            max_fo4_index = i
    print("Max FO4: {} on signal {} from cell {}".format(
        max_fo4, pin_pretty_name(max_fo4_index), output_pin_last_cell[max_fo4_index]["name"]))
    print(
        "\t- max F04 on the same signal: {}".format(output_pin_max_fo4[max_fo4_index]))
    print(
        "\t- max chain on the same signal: {}".format(output_pin_max_cell[max_fo4_index]))
    print(
        "\t- min F04 on the same signal: {}".format(output_pin_min_fo4[max_fo4_index]))
    print(
        "\t- min chain on the same signal: {}".format(output_pin_min_cell[max_fo4_index]))

    min_fo4 = 999999999
    min_fo4_index = 0
    for i in output_pin_min_fo4:
        if output_pin_min_fo4[i] < min_fo4:
            min_fo4 = output_pin_min_fo4[i]
            min_fo4_index = i
    print("Min FO4: {} on signal {} from cell {}".format(
        min_fo4, pin_pretty_name(min_fo4_index), output_pin_last_cell[min_fo4_index]["name"]))
    print(
        "\t- max F04 on the same signal: {}".format(output_pin_max_fo4[min_fo4_index]))
    print(
        "\t- max chain on the same signal: {}".format(output_pin_max_cell[min_fo4_index]))
    print(
        "\t- min F04 on the same signal: {}".format(output_pin_min_fo4[min_fo4_index]))
    print(
        "\t- min chain on the same signal: {}".format(output_pin_min_cell[min_fo4_index]))

    # TODO
    # Rename output signal with the netnames
