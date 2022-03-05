// A nand is expected to have a Fanout of 4/3
// If it has N inputs: (n+2)/3

module NAND(output y, input a, input b);

// data flow modeling
assign y = ~(a&b);

endmodule
