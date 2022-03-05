// A nand is expected to have a Fanout of 4/3
// If it has N inputs: (n+2)/3

module NAND_3(output y, input a, input b);

// behavioral modeling
always @ (a or b)
begin
	if (a == 1'b1 & b == 1'b1)
		y = 1'b0;
	else
		y = 1'b1;
end

endmodule
