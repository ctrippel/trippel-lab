module counter #(parameter int WID = 4) (
  input clk_i, input rst_ni, input up,  
  input down, output full_o
); 
// cntr is a flop of size WID, 
// counting from 0 to 2^WID - 1
// <>_q/n: current/next state 
logic [WID-1:0] cntr_q, cntr_n; 
// unary AND over all bits of cntr_q
assign full_o = &cntr_q;

always_comb begin
  cntr_n = cntr_q;
  if (up)        
    cntr_n = cntr_n + 1;
  if (down)      
    cntr_n = cntr_n - 1;
end 
// Assignment happens when clk_i rises to 1. 
always_ff @(posedge clk_i) begin
  cntr_q <= (!rst_ni) ? '0 : cntr_n;
end
// Assertion Definition
`ifdef ABV_ON
UNDERFLOW: assert property (@(posedge clk_i) 
// cycle i: cntr_q is 0 and up is 0
((cntr_q == '0) && (up == 1'b0)) |=> 
// cycle i+1: cntr_q remains
(cntr_q == '0));

INPUT_UP_INTERFACE: assume property (1'b1);  

// full_o stays 1 if down is 0 
OVERFLOW: assert property (@(posedge clk_i)
  (full_o == 1'b1 & (down == 1'b0)) |=> full_o);

// full_o is 0 some cycle followed by 1 in next cycle and some cycle later 0 again  
EVER_FULL: cover property (@(posedge clk_i) !full_o ##1 full_o ##[1:$] !full_o);
`endif // ABV_ON
endmodule 
