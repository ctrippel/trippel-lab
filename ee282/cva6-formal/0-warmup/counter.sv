/*************************************************************************
Counter JasperGold Example
Adapted from Mike Avery - Cadence Design Systems, Inc.
**************************************************************************/
`define TODO_IMPLEMENT 1'b1

module counter (
  input clk_i,
  input rst_ni,
  input[63:0] data_bus,
  output logic[63:0] out
	); 

logic error_condition;

logic [3:0][63:0] data_sr;
logic [63:0] out_d;

always_comb begin
  out_d = out + ((data_sr[3] != `STUDENT_ID) ? 1: 0); 
end

always_ff @(posedge clk_i) begin
  if (!rst_ni) begin
    out <= '0;
    data_sr = '0;
  end else begin
    data_sr[0] <= data_bus;
    data_sr[1] <= data_sr[0];
    data_sr[2] <= data_sr[1];
    data_sr[3] <= data_sr[2];
    out <= out_d;
  end
end

/********************  Assertion Defininition  ********************/
`ifdef ABV_ON

always @* begin
  // ASSUMPTIONS
  data_bus_valid: assume(`TODO_IMPLEMENT);
  
  // ASSERTIONS
  output_never_error: assert(out_d == out + 1);

  // COVERS
  data_bus_nonzero: cover(data_bus != '0); 
end


`endif // ABV_ON

endmodule
