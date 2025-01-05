# Flist.counter is a text file containing a list of system verilog files, and some verilog macros
analyze -sv09 -f Flist.fifo
elaborate             ;# synthesize and read the netlist and extract verification tasks 
clock clk_i           ;# clock <clk> to specify the clock 
reset !rst_ni         ;# reset <expr> to specify reset condition for the DUV
prove -all            ;# Evaluate all properties (asserts, covers) found during `analyze`
report -summary -results -file jg_summary.txt -force    ;# generate a result report
