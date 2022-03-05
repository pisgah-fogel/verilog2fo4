module test_1 (
    input a, b,
    input e, // not connected
    output c,
    output d, // not connected 1'bx
    output f, // alway 1
    output g
  );

  assign c = !(a & b);
  assign f = !(c & d);
  assign g = !(a | b);

endmodule
