module fifo #(
  parameter NUM_ENTRY = 4, 
  parameter DATAW = 8) (
  input clk_i,
  input rst_ni,
  input [DATAW-1:0] data_i,
  input valid_i,
  input pop_i, 
  output [DATAW-1:0] popped_data,
  output empty_o,
  output full_o
  );
// rPtr_q points to the oldest valid entry 
// wPtr_q points to the entry location for next valid entry to be allocated
// cnt_q count number of valid entries, value can take from 0 to NUM_ENTRY
logic [DATAW-1:0] queue_q [0:NUM_ENTRY-1], queue_n [0:NUM_ENTRY-1];
logic [$clog2(NUM_ENTRY)-1:0] rPtr_q, rPtr_n;
logic [$clog2(NUM_ENTRY)-1:0] wPtr_q, wPtr_n;
logic [$clog2(NUM_ENTRY)-1:0] cnt_q, cnt_n;     // TODO
// rPtr_q == wPtr_q |-> either empty or full
assign popped_data = queue_q[rPtr_q];
assign empty_o = (cnt_q == '0);
assign full_o = (cnt_q == NUM_ENTRY);

always_comb begin
  queue_n = queue_q;
  wPtr_n = wPtr_q;
  rPtr_n = rPtr_q;
  cnt_n = cnt_q;
  if (valid_i) begin
    queue_n[wPtr_q] = data_i; 
    wPtr_n = wPtr_q + 1'b1;
    cnt_n = cnt_n + 1'b1;
  end 

  if (pop_i) begin
    rPtr_n = rPtr_n + 1'b1;
    cnt_n = cnt_n - 1'b1; 
  end 
end

always_ff @(posedge clk_i) begin
  if (~rst_ni) begin
    queue_q <= '{default:'0};
    rPtr_q <= '0;
    wPtr_q <= '0;
    cnt_q <= '0;
  end else begin
    queue_q <= queue_n;
    rPtr_q <= rPtr_n;
    wPtr_q <= wPtr_n;
    cnt_q <= cnt_n;
  end 
end 

`ifdef ABV_ON
// Part 1
EVER_FULL: cover property (@(posedge clk_i) full_o);
CONT_PUSH: cover property (@(posedge clk_i) cnt_q == 0 ##0 
  (pop_i == 0 && valid_i == 1) [*NUM_ENTRY] ##1
  full_o == 1'b0); // BUG

// Part 2
NO_UNDERFLOW: assert property (0); //
NO_OVERFLOW: assert property (@(posedge clk_i)
  !(cnt_q == (NUM_ENTRY + 1)));
// TODO
HDSHK_1: assume property (1);
HDSHK_2: assume property (1);

// Part 3
logic [DATAW-1:0] d1, d2;
wire e1 = ((valid_i == 1'b1) && (data_i == d1));
wire e2 = ((valid_i == 1'b1) && (data_i == d2));
d1_const: assume property (@(posedge clk_i) d1 == $past(d1));
d2_const: assume property (@(posedge clk_i) d2 == $past(d2));
d1_dff_d2: assume property (d1 != d2);

reg e2_hpn;
always_ff @(posedge clk_i) begin
  if (!rst_ni)
    e2_hpn <= 1'b0;
  else if (e2)
    e2_hpn <= 1'b1;
end 
d1_in_hb_d2_in: assume property (@(posedge clk_i) e1 |-> !e2_hpn);

wire e3 = (pop_i == 1'b1) && (popped_data == d1);
wire e4 = 1;  // TODO
// TODO: Set up some history variable on d2 appearing at the output 
d1_out_hb_d2_out: assert property (@(posedge clk_i)
  // popping and get d1 as read data 
   e3 |->
    0 
    // TODO: d2 shouldn't have appeared 
    // Plug in the history variable set up
  );
`endif
endmodule
