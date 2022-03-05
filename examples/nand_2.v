// A nand is expected to have a Fanout of 4/3
// If it has N inputs: (n+2)/3

module NAND_2(output y, input a, input b);

// gate level modeling
wire yd;
and(yd, a, b);
not(y, yd);

endmodule
