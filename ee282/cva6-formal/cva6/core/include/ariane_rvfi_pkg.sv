// Copyright 2020 Thales DIS design services SAS
//
// Licensed under the Solderpad Hardware Licence, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// SPDX-License-Identifier: Apache-2.0 WITH SHL-2.0
// You may obtain a copy of the License at https://solderpad.org/licenses/
//
// Original Author: Jean-Roch COULON - Thales

package ariane_rvfi_pkg;

  localparam ILEN = 32;

  typedef struct packed {
    logic                       valid;
    logic [64-1:0]              order;
    logic [ILEN-1:0]            insn;
    logic                       trap;
    logic [riscv::XLEN-1:0]     cause;
    logic                       halt;
    logic                       intr;
    logic [1:0]                 mode;
    logic [1:0]                 ixl;
    logic [4:0]                 rs1_addr;
    logic [4:0]                 rs2_addr;
    logic [riscv::XLEN-1:0]     rs1_rdata;
    logic [riscv::XLEN-1:0]     rs2_rdata;
    logic [4:0]                 rd_addr;
    logic [riscv::XLEN-1:0]     rd_wdata;

    logic [riscv::XLEN-1:0]     pc_rdata;
    logic [riscv::XLEN-1:0]     pc_wdata;

    logic [riscv::VLEN-1:0]     mem_addr;
    logic [riscv::PLEN-1:0]     mem_paddr;
    logic [(riscv::XLEN/8)-1:0] mem_rmask;
    logic [(riscv::XLEN/8)-1:0] mem_wmask;
    logic [riscv::XLEN-1:0]     mem_rdata;
    logic [riscv::XLEN-1:0]     mem_wdata;
  } rvfi_port_t;

  typedef struct packed {
    logic                       valid;
    logic                       trap;
    logic [4:0]                 rs1_addr;
    logic [4:0]                 rs2_addr;
    logic [riscv::XLEN-1:0]     rs1_rdata;
    logic [riscv::XLEN-1:0]     rs2_rdata;
    logic [4:0]                 rd_addr;
    logic [riscv::XLEN-1:0]     rd_wdata;

    logic [riscv::XLEN-1:0]     pc_wdata;

    logic [riscv::VLEN-1:0]     mem_addr;
    logic [(riscv::XLEN/8)-1:0] mem_rmask;
    logic [(riscv::XLEN/8)-1:0] mem_wmask;
    logic [riscv::XLEN-1:0]     mem_wdata;
  } rvfi_spec_port_t;

endpackage
