import ariane_pkg::*;
module rvfi_wrapper(
    input   clk_i,
    input   rst_ni, 
    output ariane_rvfi_pkg::rvfi_port_t rvfi_o
    // EE282_TODO: Add insn field
);

    ariane_axi::req_t    axi_req;
    ariane_axi::resp_t   axi_resp;

    logic [riscv::VLEN-1:0]       boot_addr_i = '0;  // reset boot address
    logic [riscv::XLEN-1:0]       hart_id_i = '0;    // hart id in a multicore environment (reflected in a CSR)

    // Interrupt inputs
    logic [1:0]                   irq_i = '0;        // level sensitive IR lines, mip & sip (async)
    logic                         ipi_i = '0;        // inter-processor interrupts (async)
    // Timer facilities
    logic                         time_irq_i = '0;   // timer interrupt in (async)
    logic                         debug_req_i = '0;  // debug request (async)

    cva6 i_cva6 (
        .clk_i                ( clk_i                     ),
        .rst_ni               ( rst_ni                    ),
        .boot_addr_i          ( boot_addr_i               ),
        .hart_id_i            ( hart_id_i                 ),
        .irq_i                ( irq_i                     ),
        .ipi_i                ( ipi_i                     ),
        .time_irq_i           ( time_irq_i                ),
        .debug_req_i          ( debug_req_i               ),
        .rvfi_o               ( rvfi_o                    ),
        .axi_req_o            ( axi_req                   ),
        .axi_resp_i           ( axi_resp                  )
        // EE282_TODO: Add insn field
    );
    
endmodule