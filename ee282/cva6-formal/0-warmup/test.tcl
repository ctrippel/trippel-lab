# Run JG with a TCl file: jg foo.tcl
# To get help about the tcl command syntax
# use the help command "help" at the JG console
# This will list an overview of all commands.
# To get details about individual command use
# help in combination with the command name and its options.
# For example "help assert"

# Clear previous run
clear -all

# Analyze RTL files
analyze -sv -f Flist.counter

# Elaborate
elaborate

# Initialization
# Clock specification
# clock pin is called "clk"
# duty cycle is 1:1 by default
clock clk_i

# Define reset condition
# reset pin is called rst_n, active low
reset !rst_ni

# Start the verification
prove -all

report -summary -results -file jg_summary.txt -force

