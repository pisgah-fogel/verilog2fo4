
// shortest path is 2 gates (d and c)
module test_1 (
    input a, b, e,
    output c,
    output d,
    output f
  );

  assign c = !(a & b);
  assign d = !(a | e);
  assign f = !(c & d);

endmodule
