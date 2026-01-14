#!/usr/bin/env python3
#
# Copyright (C) 2017  Claire Xenia Wolf <claire@yosyshq.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from functools import wraps
import inspect

current_isa = []
isa_database = dict()
defaults_cache = None

MISA_A = 1 <<  0 # Atomic
MISA_B = 1 <<  1 # -reserved-
MISA_C = 1 <<  2 # Compressed
MISA_D = 1 <<  3 # Double-precision float
MISA_E = 1 <<  4 # RV32E base ISA
MISA_F = 1 <<  5 # Single-precision float
MISA_G = 1 <<  6 # Additional std extensions
MISA_H = 1 <<  7 # -reserved-
MISA_I = 1 <<  8 # RV32I/RV64I/RV128I base ISA
MISA_J = 1 <<  9 # -reserved-
MISA_K = 1 << 10 # -reserved-
MISA_L = 1 << 11 # -reserved-
MISA_M = 1 << 12 # Muliply/Divide
MISA_N = 1 << 13 # User-level interrupts
MISA_O = 1 << 14 # -reserved-
MISA_P = 1 << 15 # -reserved-
MISA_Q = 1 << 16 # Quad-precision float
MISA_R = 1 << 17 # -reserved-
MISA_S = 1 << 18 # Supervisor mode
MISA_T = 1 << 19 # -reserved-
MISA_U = 1 << 20 # User mode
MISA_V = 1 << 21 # -reserved-
MISA_W = 1 << 22 # -reserved-
MISA_X = 1 << 23 # Non-std extensions
MISA_Y = 1 << 24 # -reserved-
MISA_Z = 1 << 25 # -reserved-


def gencover(func):
    sig = inspect.signature(func)
    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        insn = bound.arguments["insn"]
  
    return wrapper

def gencheck(func):
    sig = inspect.signature(func)
    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        insn = bound.arguments["insn"]
        with open("insn_%s.tcl" % insn, "w+") as f:
            print(f"analyze +define+RISCV_FORMAL_INSN_MODEL=insn_{insn} -f Flist.formal -sv insns/insn_{insn}.v",file=f)
            print(f"elaborate -bbox_m {{wt_cache_subsystem wt_axi_adapter wt_dcache_mem sram}}",file=f)
            print(f"clock clk_i",file=f)
            print(f"reset !rst_ni",file=f)
            print(f"set_engine_mode {{Ht}}",file=f)
            print(f"set_engineH_first_trace_attempt 5",file=f)
            print(f"prove -all -cover ",file=f)
            print(f"set_max_trace_length 13",file=f)
            print(f"set_prove_time_limit 0s",file=f)
            print(f"load_radix_file radix.txt", file=f)
            print(f"set_engine_mode {{I N}}",file=f)
            print(f"prove -all -assert",file=f)
            print(f"report -results -file insns/insn_{insn}.txt -force",file=f)
            
        func(*args, **kwargs)
    return wrapper

def header(f, insn, isa_mode=False):
    if not isa_mode:
        global isa_database
        for isa in current_isa:
            if isa not in isa_database:
                isa_database[isa] = set()
            isa_database[isa].add(insn)

    global defaults_cache
    defaults_cache = dict()

    print("// DO NOT EDIT -- auto-generated from riscv-formal/insns/generate.py", file=f)
    print("", file=f)
    print("import ariane_pkg::*;", file=f)
    if isa_mode:
        print("module isa_%s (" % insn, file=f)
    else:
        print("module insn_%s (" % insn, file=f)

    print("  input ariane_rvfi_pkg::rvfi_port_t rvfi_i,", file=f)
    print("  output ariane_rvfi_pkg::rvfi_spec_port_t rvfi_spec_o", file=f)

    print(");", file=f)

    defaults_cache["rvfi_spec_o.valid"] = "0"
    defaults_cache["rvfi_spec_o.rs1_addr"] = "0"
    defaults_cache["rvfi_spec_o.rs2_addr"] = "0"
    defaults_cache["rvfi_spec_o.rd_addr"] = "0"
    defaults_cache["rvfi_spec_o.rd_wdata"] = "0"
    defaults_cache["rvfi_spec_o.pc_wdata"] = "0"
    defaults_cache["rvfi_spec_o.trap"] = "!misa_ok"
    defaults_cache["rvfi_spec_o.mem_addr"] = "0"
    defaults_cache["rvfi_spec_o.mem_rmask"] = "0"
    defaults_cache["rvfi_spec_o.mem_wmask"] = "0"
    defaults_cache["rvfi_spec_o.mem_wdata"] = "0"

def assign(f, sig, val):
    print("  assign %s = %s;" % (sig, val), file=f)

    if sig in defaults_cache:
        del defaults_cache[sig]

def misa_check(f, mask, ialign16=False):
    print("", file=f)
    print("`ifdef RISCV_FORMAL_CSR_MISA", file=f)
    print("  wire misa_ok = (rvfi_i.csr_misa_rdata & `RISCV_FORMAL_XLEN'h %x) == `RISCV_FORMAL_XLEN'h %x;" % (mask, mask), file=f)
    print("  assign rvfi_spec_o.csr_misa_rmask = `RISCV_FORMAL_XLEN'h %x;" % ((mask|MISA_C) if ialign16 else mask), file=f)
    if ialign16:
        print("  wire ialign16 = (rvfi_i.csr_misa_rdata & `RISCV_FORMAL_XLEN'h %x) != `RISCV_FORMAL_XLEN'h 0;" % (MISA_C), file=f)
    print("`else", file=f)
    print("  wire misa_ok = 1;", file=f)
    if ialign16:
        print("`ifdef RISCV_FORMAL_COMPRESSED", file=f)
        print("  wire ialign16 = 1;", file=f)
        print("`else", file=f)
        print("  wire ialign16 = 0;", file=f)
        print("`endif", file=f)
    print("`endif", file=f)

def footer(f):
    def default_assign(sig):
        if sig in defaults_cache:
            print("  assign %s = %s;" % (sig, defaults_cache[sig]), file=f)

    if len(defaults_cache) != 0:
        print("", file=f)
        print("  // default assignments", file=f)

        default_assign("rvfi_spec_o.valid")
        default_assign("rvfi_spec_o.rs1_addr")
        default_assign("rvfi_spec_o.rs2_addr")
        default_assign("rvfi_spec_o.rd_addr")
        default_assign("rvfi_spec_o.rd_wdata")
        default_assign("rvfi_spec_o.pc_wdata")
        default_assign("rvfi_spec_o.trap")
        default_assign("rvfi_spec_o.mem_addr")
        default_assign("rvfi_spec_o.mem_rmask")
        default_assign("rvfi_spec_o.mem_wmask")
        default_assign("rvfi_spec_o.mem_wdata")

    print("endmodule", file=f)

def format_r(f):
    print("", file=f)
    print("  // R-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16 >> 16;", file=f)
    print("  wire [6:0] insn_funct7 = rvfi_i.insn[31:25];", file=f)
    print("  wire [4:0] insn_rs2    = rvfi_i.insn[24:20];", file=f)
    print("  wire [4:0] insn_rs1    = rvfi_i.insn[19:15];", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[14:12];", file=f)
    print("  wire [4:0] insn_rd     = rvfi_i.insn[11: 7];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_i.insn[ 6: 0];", file=f)

def format_ra(f):
    print("", file=f)
    print("  // R-type instruction format (atomics variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16 >> 16;", file=f)
    print("  wire [6:0] insn_funct5 = rvfi_i.insn[31:27];", file=f)
    print("  wire       insn_aq     = rvfi_i.insn[26];", file=f)
    print("  wire       insn_rl     = rvfi_i.insn[25];", file=f)
    print("  wire [4:0] insn_rs2    = rvfi_i.insn[24:20];", file=f)
    print("  wire [4:0] insn_rs1    = rvfi_i.insn[19:15];", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[14:12];", file=f)
    print("  wire [4:0] insn_rd     = rvfi_i.insn[11: 7];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_i.insn[ 6: 0];", file=f)

def format_i(f):
    print("", file=f)
    print("  // I-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16 >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed(rvfi_i.insn[31:20]);", file=f)
    print("  wire [4:0] insn_rs1    = rvfi_i.insn[19:15];", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[14:12];", file=f)
    print("  wire [4:0] insn_rd     = rvfi_i.insn[11: 7];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_i.insn[ 6: 0];", file=f)

def format_i_shift(f):
    print("", file=f)
    print("  // I-type instruction format (shift variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16 >> 16;", file=f)
    print("  wire [6:0] insn_funct6 = rvfi_i.insn[31:26];", file=f)
    print("  wire [5:0] insn_shamt  = rvfi_i.insn[25:20];", file=f)
    print("  wire [4:0] insn_rs1    = rvfi_i.insn[19:15];", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[14:12];", file=f)
    print("  wire [4:0] insn_rd     = rvfi_i.insn[11: 7];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_i.insn[ 6: 0];", file=f)

def format_s(f):
    print("", file=f)
    print("  // S-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16 >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_i.insn[31:25], rvfi_i.insn[11:7]});", file=f)
    print("  wire [4:0] insn_rs2    = rvfi_i.insn[24:20];", file=f)
    print("  wire [4:0] insn_rs1    = rvfi_i.insn[19:15];", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[14:12];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_i.insn[ 6: 0];", file=f)

def format_sb(f):
    print("", file=f)
    print("  // SB-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16 >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_i.insn[31], rvfi_i.insn[7], rvfi_i.insn[30:25], rvfi_i.insn[11:8], 1'b0});", file=f)
    print("  wire [4:0] insn_rs2    = rvfi_i.insn[24:20];", file=f)
    print("  wire [4:0] insn_rs1    = rvfi_i.insn[19:15];", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[14:12];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_i.insn[ 6: 0];", file=f)

def format_u(f):
    print("", file=f)
    print("  // U-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16 >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_i.insn[31:12], 12'b0});", file=f)
    print("  wire [4:0] insn_rd     = rvfi_i.insn[11:7];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_i.insn[ 6:0];", file=f)

def format_uj(f):
    print("", file=f)
    print("  // UJ-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16 >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_i.insn[31], rvfi_i.insn[19:12], rvfi_i.insn[20], rvfi_i.insn[30:21], 1'b0});", file=f)
    print("  wire [4:0] insn_rd     = rvfi_i.insn[11:7];", file=f)
    print("  wire [6:0] insn_opcode = rvfi_i.insn[6:0];", file=f)

def format_cr(f):
    print("", file=f)
    print("  // CI-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    print("  wire [3:0] insn_funct4 = rvfi_i.insn[15:12];", file=f)
    print("  wire [4:0] insn_rs1_rd = rvfi_i.insn[11:7];", file=f)
    print("  wire [4:0] insn_rs2 = rvfi_i.insn[6:2];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

def format_ci(f):
    print("", file=f)
    print("  // CI-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_i.insn[12], rvfi_i.insn[6:2]});", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[15:13];", file=f)
    print("  wire [4:0] insn_rs1_rd = rvfi_i.insn[11:7];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

def format_ci_sp(f):
    print("", file=f)
    print("  // CI-type instruction format (SP variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_i.insn[12], rvfi_i.insn[4:3], rvfi_i.insn[5], rvfi_i.insn[2], rvfi_i.insn[6], 4'b0});", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[15:13];", file=f)
    print("  wire [4:0] insn_rs1_rd = rvfi_i.insn[11:7];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

def format_ci_lui(f):
    print("", file=f)
    print("  // CI-type instruction format (LUI variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_i.insn[12], rvfi_i.insn[6:2], 12'b0});", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[15:13];", file=f)
    print("  wire [4:0] insn_rs1_rd = rvfi_i.insn[11:7];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

def format_ci_sri(f):
    print("", file=f)
    print("  // CI-type instruction format (SRI variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    print("  wire [5:0] insn_shamt = {rvfi_i.insn[12], rvfi_i.insn[6:2]};", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[15:13];", file=f)
    print("  wire [1:0] insn_funct2 = rvfi_i.insn[11:10];", file=f)
    print("  wire [4:0] insn_rs1_rd = {1'b1, rvfi_i.insn[9:7]};", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

def format_ci_sli(f):
    print("", file=f)
    print("  // CI-type instruction format (SLI variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    print("  wire [5:0] insn_shamt = {rvfi_i.insn[12], rvfi_i.insn[6:2]};", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[15:13];", file=f)
    print("  wire [4:0] insn_rs1_rd = rvfi_i.insn[11:7];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

def format_ci_andi(f):
    print("", file=f)
    print("  // CI-type instruction format (ANDI variation)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_i.insn[12], rvfi_i.insn[6:2]});", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[15:13];", file=f)
    print("  wire [1:0] insn_funct2 = rvfi_i.insn[11:10];", file=f)
    print("  wire [4:0] insn_rs1_rd = {1'b1, rvfi_i.insn[9:7]};", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

def format_ci_lsp(f, numbytes):
    print("", file=f)
    print("  // CI-type instruction format (LSP variation, %d bit version)" % (8*numbytes), file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    if numbytes == 4:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_i.insn[3:2], rvfi_i.insn[12], rvfi_i.insn[6:4], 2'b00};", file=f)
    elif numbytes == 8:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_i.insn[4:2], rvfi_i.insn[12], rvfi_i.insn[6:5], 3'b000};", file=f)
    else:
        assert False
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[15:13];", file=f)
    print("  wire [4:0] insn_rd = rvfi_i.insn[11:7];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

def format_cl(f, numbytes):
    print("", file=f)
    print("  // CL-type instruction format (%d bit version)" % (8*numbytes), file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    if numbytes == 4:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_i.insn[5], rvfi_i.insn[12:10], rvfi_i.insn[6], 2'b00};", file=f)
    elif numbytes == 8:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_i.insn[6:5], rvfi_i.insn[12:10], 3'b000};", file=f)
    else:
        assert False
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[15:13];", file=f)
    print("  wire [4:0] insn_rs1 = {1'b1, rvfi_i.insn[9:7]};", file=f)
    print("  wire [4:0] insn_rd = {1'b1, rvfi_i.insn[4:2]};", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

def format_css(f, numbytes):
    print("", file=f)
    print("  // CSS-type instruction format (%d bit version)" % (8*numbytes), file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    if numbytes == 4:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_i.insn[8:7], rvfi_i.insn[12:9], 2'b00};", file=f)
    elif numbytes == 8:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_i.insn[9:7], rvfi_i.insn[12:10], 3'b000};", file=f)
    else:
        assert False
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[15:13];", file=f)
    print("  wire [4:0] insn_rs2 = rvfi_i.insn[6:2];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

def format_cs(f, numbytes):
    print("", file=f)
    print("  // CS-type instruction format (%d bit version)" % (8*numbytes), file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    if numbytes == 4:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_i.insn[5], rvfi_i.insn[12:10], rvfi_i.insn[6], 2'b00};", file=f)
    elif numbytes == 8:
        print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_i.insn[6:5], rvfi_i.insn[12:10], 3'b000};", file=f)
    else:
        assert False
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[15:13];", file=f)
    print("  wire [4:0] insn_rs1 = {1'b1, rvfi_i.insn[9:7]};", file=f)
    print("  wire [4:0] insn_rs2 = {1'b1, rvfi_i.insn[4:2]};", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

def format_cs_alu(f):
    print("", file=f)
    print("  // CS-type instruction format (ALU version)", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    print("  wire [5:0] insn_funct6 = rvfi_i.insn[15:10];", file=f)
    print("  wire [1:0] insn_funct2 = rvfi_i.insn[6:5];", file=f)
    print("  wire [4:0] insn_rs1_rd = {1'b1, rvfi_i.insn[9:7]};", file=f)
    print("  wire [4:0] insn_rs2 = {1'b1, rvfi_i.insn[4:2]};", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

def format_ciw(f):
    print("", file=f)
    print("  // CIW-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = {rvfi_i.insn[10:7], rvfi_i.insn[12:11], rvfi_i.insn[5], rvfi_i.insn[6], 2'b00};", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[15:13];", file=f)
    print("  wire [4:0] insn_rd = {1'b1, rvfi_i.insn[4:2]};", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

def format_cb(f):
    print("", file=f)
    print("  // CB-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_i.insn[12], rvfi_i.insn[6:5], rvfi_i.insn[2], rvfi_i.insn[11:10], rvfi_i.insn[4:3], 1'b0});", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[15:13];", file=f)
    print("  wire [4:0] insn_rs1 = {1'b1, rvfi_i.insn[9:7]};", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

def format_cj(f):
    print("", file=f)
    print("  // CJ-type instruction format", file=f)
    print("  wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = rvfi_i.insn >> 16;", file=f)
    print("  wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({rvfi_i.insn[12], rvfi_i.insn[8], rvfi_i.insn[10], rvfi_i.insn[9],", file=f)
    print("      rvfi_i.insn[6], rvfi_i.insn[7], rvfi_i.insn[2], rvfi_i.insn[11], rvfi_i.insn[5], rvfi_i.insn[4], rvfi_i.insn[3], 1'b0});", file=f)
    print("  wire [2:0] insn_funct3 = rvfi_i.insn[15:13];", file=f)
    print("  wire [1:0] insn_opcode = rvfi_i.insn[1:0];", file=f)

@gencheck
def insn_lui(insn="lui", misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_u(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_opcode == 7'b 0110111")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        assign(f, "rvfi_spec_o.rd_wdata", "insn_imm")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 4")

        footer(f)

@gencheck
def insn_auipc(insn="auipc", misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_u(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_opcode == 7'b 0010111")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        assign(f, "rvfi_spec_o.rd_wdata", "rvfi_i.pc_rdata + insn_imm")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 4")

        footer(f)

@gencheck
def insn_jal(insn="jal", misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_uj(f)
        misa_check(f, misa,  ialign16=True)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] next_pc = rvfi_i.pc_rdata + insn_imm;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_opcode == 7'b 1101111")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        assign(f, "rvfi_spec_o.rd_wdata", "rvfi_i.pc_rdata + 4")
        assign(f, "rvfi_spec_o.pc_wdata", "next_pc")
        assign(f, "rvfi_spec_o.trap", "(ialign16 ? (next_pc[0] != 0) : (next_pc[0] != 0)) || !misa_ok")

        footer(f)

@gencheck
def insn_jalr(insn="jalr", misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_i(f)
        misa_check(f, misa, ialign16=True)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] next_pc = (rvfi_i.rs1_rdata + insn_imm) & ~1;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b 000 && insn_opcode == 7'b 1100111")
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        assign(f, "rvfi_spec_o.rd_wdata", "rvfi_i.pc_rdata + 4")
        assign(f, "rvfi_spec_o.pc_wdata", "next_pc")
        assign(f, "rvfi_spec_o.trap", "(ialign16 ? (next_pc[0] != 0) : (next_pc[0] != 0)) || !misa_ok")

        footer(f)

@gencheck
def insn_b(insn, funct3, expr, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_sb(f)
        misa_check(f, misa, ialign16=True)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire cond = %s;" % expr, file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] next_pc = cond ? rvfi_i.pc_rdata + insn_imm : rvfi_i.pc_rdata + 4;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 7'b 1100011" % funct3)
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rs2_addr", "insn_rs2")
        assign(f, "rvfi_spec_o.pc_wdata", "next_pc")
        assign(f, "rvfi_spec_o.trap", "(ialign16 ? (next_pc[0] != 0) : (next_pc[0] != 0)) || !misa_ok")

        footer(f)

@gencheck
def insn_l(insn, funct3, numbytes, signext, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_i(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("`ifdef RISCV_FORMAL_ALIGNED_MEM", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_i.rs1_rdata + insn_imm;", file=f)
        print("  wire [%d:0] result = rvfi_i.mem_rdata >> (8*(addr-rvfi_spec_o.mem_addr));" % (8*numbytes-1), file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 7'b 0000011" % funct3)
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        assign(f, "rvfi_spec_o.mem_addr", "addr & ~(`RISCV_FORMAL_XLEN/8-1)")
        assign(f, "rvfi_spec_o.mem_rmask", "((1 << %d)-1) << (addr-rvfi_spec_o.mem_addr)" % numbytes)
        if signext:
            assign(f, "rvfi_spec_o.rd_wdata", "$signed(result)")
        else:
            assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 4")
        assign(f, "rvfi_spec_o.trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`else", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_i.rs1_rdata + insn_imm;", file=f)
        print("  wire [%d:0] result = rvfi_i.mem_rdata;" % (8*numbytes-1), file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && insn_funct3 == 3'b %s && insn_opcode == 7'b 0000011" % funct3)
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        assign(f, "rvfi_spec_o.mem_addr", "addr")
        assign(f, "rvfi_spec_o.mem_rmask", "((1 << %d)-1)" % numbytes)
        if signext:
            assign(f, "rvfi_spec_o.rd_wdata", "$signed(result)")
        else:
            assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 4")
        assign(f, "rvfi_spec_o.trap", "!misa_ok")

        print("`endif", file=f)

        footer(f)

@gencheck
def insn_s(insn, funct3, numbytes, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_s(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("`ifdef RISCV_FORMAL_ALIGNED_MEM", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_i.rs1_rdata + insn_imm;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 7'b 0100011" % funct3)
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rs2_addr", "insn_rs2")
        assign(f, "rvfi_spec_o.mem_addr", "addr & ~(`RISCV_FORMAL_XLEN/8-1)")
        assign(f, "rvfi_spec_o.mem_wmask", "((1 << %d)-1) << (addr-rvfi_spec_o.mem_addr)" % numbytes)
        assign(f, "rvfi_spec_o.mem_wdata", "rvfi_i.rs2_rdata << (8*(addr-rvfi_spec_o.mem_addr))")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 4")
        assign(f, "rvfi_spec_o.trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`else", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_i.rs1_rdata + insn_imm;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 7'b 0100011" % funct3)
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rs2_addr", "insn_rs2")
        assign(f, "rvfi_spec_o.mem_addr", "addr")
        assign(f, "rvfi_spec_o.mem_wmask", "((1 << %d)-1)" % numbytes)
        assign(f, "rvfi_spec_o.mem_wdata", "rvfi_i.rs2_rdata")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 4")
        assign(f, "rvfi_spec_o.trap", "!misa_ok")

        print("`endif", file=f)

        footer(f)

@gencheck
def insn_imm(insn, funct3, expr, wmode=False, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_i(f)
        misa_check(f, misa)

        if wmode:
            result_range = "31:0"
            opcode = "0011011"
        else:
            result_range = "`RISCV_FORMAL_XLEN-1:0"
            opcode = "0010011"

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [%s] result = %s;" % (result_range, expr), file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 7'b %s" % (funct3, opcode))
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        if wmode:
            assign(f, "rvfi_spec_o.rd_wdata", "{{`RISCV_FORMAL_XLEN-32{result[31]}}, result}")
        else:
            assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 4")

        footer(f)

@gencheck
def insn_shimm(insn, funct6, funct3, expr, wmode=False, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_i_shift(f)
        misa_check(f, misa)

        if wmode:
            xtra_shamt_check = "!insn_shamt[5]"
            result_range = "31:0"
            opcode = "0011011"
        else:
            xtra_shamt_check = "(!insn_shamt[5] || `RISCV_FORMAL_XLEN == 64)"
            result_range = "`RISCV_FORMAL_XLEN-1:0"
            opcode = "0010011"

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [%s] result = %s;" % (result_range, expr), file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct6 == 6'b %s && insn_funct3 == 3'b %s && insn_opcode == 7'b %s && %s" % (funct6, funct3, opcode, xtra_shamt_check))
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        if wmode:
            assign(f, "rvfi_spec_o.rd_wdata", "{{`RISCV_FORMAL_XLEN-32{result[31]}}, result}")
        else:
            assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 4")

        footer(f)

@gencheck
def insn_alu(insn, funct7, funct3, expr, alt_add=None, alt_sub=None, shamt=False, wmode=False, misa=0):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_r(f)
        misa_check(f, misa)

        if wmode:
            result_range = "31:0"
            opcode = "0111011"
        else:
            result_range = "`RISCV_FORMAL_XLEN-1:0"
            opcode = "0110011"

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        if shamt:
            if wmode:
                print("  wire [4:0] shamt = rvfi_i.rs2_rdata[4:0];", file=f)
            else:
                print("  wire [5:0] shamt = `RISCV_FORMAL_XLEN == 64 ? rvfi_i.rs2_rdata[5:0] : rvfi_i.rs2_rdata[4:0];", file=f)
        if alt_add is not None or alt_sub is not None:
            print("`ifdef RISCV_FORMAL_ALTOPS", file=f)
            if alt_add is not None:
                print("  wire [%s] altops_bitmask = 64'h%016x;" % (result_range, alt_add), file=f)
                print("  wire [%s] result = (rvfi_i.rs1_rdata + rvfi_i.rs2_rdata) ^ altops_bitmask;" % result_range, file=f)
            else:
                print("  wire [%s] altops_bitmask = 64'h%016x;" % (result_range, alt_sub), file=f)
                print("  wire [%s] result = (rvfi_i.rs1_rdata - rvfi_i.rs2_rdata) ^ altops_bitmask;" % result_range, file=f)
            print("`else", file=f)
            print("  wire [%s] result = %s;" % (result_range, expr), file=f)
            print("`endif", file=f)
        else:
            print("  wire [%s] result = %s;" % (result_range, expr), file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct7 == 7'b %s && insn_funct3 == 3'b %s && insn_opcode == 7'b %s" % (funct7, funct3, opcode))
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rs2_addr", "insn_rs2")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        if wmode:
            assign(f, "rvfi_spec_o.rd_wdata", "{{`RISCV_FORMAL_XLEN-32{result[31]}}, result}")
        else:
            assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 4")

        footer(f)

@gencheck
def insn_amo(insn, funct5, funct3, expr, misa=MISA_A):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ra(f)
        misa_check(f, misa)

        if funct3 == "010":
            oprange = "31:0"
            numbytes = 4
        else:
            oprange = "63:0"
            numbytes = 8

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [%s] mem_result = %s;" % (oprange, expr), file=f)
        print("  wire [%s] reg_result = rvfi_i.mem_rdata[%s];" % (oprange, oprange), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_i.rs1_rdata;", file=f)

        print("`ifdef RISCV_FORMAL_ALIGNED_MEM", file=f)

        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct5 == 5'b %s && insn_funct3 == 3'b %s && insn_opcode == 7'b 0101111" % (funct5, funct3))
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rs2_addr", "insn_rs2")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        assign(f, "rvfi_spec_o.rd_wdata", "$signed(reg_result)")
        assign(f, "rvfi_spec_o.mem_addr", "addr & ~(`RISCV_FORMAL_XLEN/8-1)")
        assign(f, "rvfi_spec_o.mem_wmask", "((1 << %d)-1) << (addr-rvfi_spec_o.mem_addr)" % numbytes)
        assign(f, "rvfi_spec_o.mem_wdata", "mem_result << (8*(addr-rvfi_spec_o.mem_addr))")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 4")
        assign(f, "rvfi_spec_o.trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`else", file=f)

        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct5 == 5'b %s && insn_funct3 == 3'b %s && insn_opcode == 7'b 0101111" % (funct5, funct3))
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rs2_addr", "insn_rs2")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        assign(f, "rvfi_spec_o.rd_wdata", "$signed(reg_result)")
        assign(f, "rvfi_spec_o.mem_addr", "addr")
        assign(f, "rvfi_spec_o.mem_wmask", "((1 << %d)-1)" % numbytes)
        assign(f, "rvfi_spec_o.mem_wdata", "mem_result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 4")
        assign(f, "rvfi_spec_o.trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`endif", file=f)

        footer(f)

@gencheck
def insn_c_addi4spn(insn="c_addi4spn", misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ciw(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = rvfi_i.rs1_rdata + insn_imm;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b 000 && insn_opcode == 2'b 00 && insn_imm")
        assign(f, "rvfi_spec_o.rs1_addr", "2")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")

        footer(f)

@gencheck
def insn_c_l(insn, funct3, numbytes, signext, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_cl(f, numbytes)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("`ifdef RISCV_FORMAL_ALIGNED_MEM", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_i.rs1_rdata + insn_imm;", file=f)
        print("  wire [%d:0] result = rvfi_i.mem_rdata >> (8*(addr-rvfi_spec_o.mem_addr));" % (8*numbytes-1), file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 00" % funct3)
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        assign(f, "rvfi_spec_o.mem_addr", "addr & ~(`RISCV_FORMAL_XLEN/8-1)")
        assign(f, "rvfi_spec_o.mem_rmask", "((1 << %d)-1) << (addr-rvfi_spec_o.mem_addr)" % numbytes)
        if signext:
            assign(f, "rvfi_spec_o.rd_wdata", "$signed(result)")
        else:
            assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")
        assign(f, "rvfi_spec_o.trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`else", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_i.rs1_rdata + insn_imm;", file=f)
        print("  wire [%d:0] result = rvfi_i.mem_rdata;" % (8*numbytes-1), file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 00" % funct3)
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        assign(f, "rvfi_spec_o.mem_addr", "addr")
        assign(f, "rvfi_spec_o.mem_rmask", "((1 << %d)-1)" % numbytes)
        if signext:
            assign(f, "rvfi_spec_o.rd_wdata", "$signed(result)")
        else:
            assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")
        assign(f, "rvfi_spec_o.trap", "!misa_ok")

        print("`endif", file=f)

        footer(f)

@gencheck
def insn_c_s(insn, funct3, numbytes, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_cs(f, numbytes)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_i.rs1_rdata + insn_imm;", file=f)
        print("`ifdef RISCV_FORMAL_ALIGNED_MEM", file=f)

        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 00" % funct3)
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rs2_addr", "insn_rs2")
        assign(f, "rvfi_spec_o.mem_addr", "addr & ~(`RISCV_FORMAL_XLEN/8-1)")
        assign(f, "rvfi_spec_o.mem_wmask", "((1 << %d)-1) << (addr-rvfi_spec_o.mem_addr)" % numbytes)
        assign(f, "rvfi_spec_o.mem_wdata", "rvfi_i.rs2_rdata << (8*(addr-rvfi_spec_o.mem_addr))")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")
        assign(f, "rvfi_spec_o.trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`else", file=f)

        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 00" % funct3)
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.rs2_addr", "insn_rs2")
        assign(f, "rvfi_spec_o.mem_addr", "addr")
        assign(f, "rvfi_spec_o.mem_wmask", "((1 << %d)-1)" % numbytes)
        assign(f, "rvfi_spec_o.mem_wdata", "rvfi_i.rs2_rdata")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")
        assign(f, "rvfi_spec_o.trap", "!misa_ok")

        print("`endif", file=f)

        footer(f)

@gencheck
def insn_c_addi(insn="c_addi", wmode=False, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        if wmode:
            print("  wire [31:0] result = rvfi_i.rs1_rdata[31:0] + insn_imm[31:0];", file=f)
            assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b 001 && insn_opcode == 2'b 01 && insn_rs1_rd != 5'd 0")
        else:
            print("  wire [`RISCV_FORMAL_XLEN-1:0] result = rvfi_i.rs1_rdata + insn_imm;", file=f)
            assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b 000 && insn_opcode == 2'b 01")
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1_rd")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rs1_rd")
        if wmode:
            assign(f, "rvfi_spec_o.rd_wdata", "{{`RISCV_FORMAL_XLEN-32{result[31]}}, result}")
        else:
            assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")

        footer(f)

@gencheck
def insn_c_jal(insn, funct3, link, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_cj(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] next_pc = rvfi_i.pc_rdata + insn_imm;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 01" % (funct3))
        if link:
            assign(f, "rvfi_spec_o.rd_addr", "5'd 1")
            assign(f, "rvfi_spec_o.rd_wdata", "rvfi_i.pc_rdata + 2")
        assign(f, "rvfi_spec_o.pc_wdata", "next_pc")

        footer(f)

@gencheck
def insn_c_li(insn="c_li", misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = insn_imm;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b 010 && insn_opcode == 2'b 01")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rs1_rd")
        assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")

        footer(f)

@gencheck
def insn_c_addi16sp(insn="c_addi16sp", misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci_sp(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = rvfi_i.rs1_rdata + insn_imm;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b 011 && insn_opcode == 2'b 01 && insn_rs1_rd == 5'd 2 && insn_imm")
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1_rd")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rs1_rd")
        assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")

        footer(f)

@gencheck
def insn_c_lui(insn="c_lui", misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci_lui(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = insn_imm;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b 011 && insn_opcode == 2'b 01 && insn_rs1_rd != 5'd 2 && insn_imm")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rs1_rd")
        assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")

        footer(f)

@gencheck
def insn_c_sri(insn, funct2, expr, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci_sri(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = %s;" % expr, file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b 100 && insn_funct2 == 2'b %s && insn_opcode == 2'b 01 && (!insn_shamt[5] || `RISCV_FORMAL_XLEN == 64)" % funct2)
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1_rd")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rs1_rd")
        assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")

        footer(f)

@gencheck
def insn_c_andi(insn="c_andi", misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci_andi(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = rvfi_i.rs1_rdata & insn_imm;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b 100 && insn_funct2 == 2'b 10 && insn_opcode == 2'b 01")
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1_rd")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rs1_rd")
        assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")

        footer(f)

@gencheck
def insn_c_alu(insn, funct6, funct2, expr, wmode=False, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_cs_alu(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        if wmode:
            print("  wire [31:0] result = %s;" % expr, file=f)
        else:
            print("  wire [`RISCV_FORMAL_XLEN-1:0] result = %s;" % expr, file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct6 == 6'b %s && insn_funct2 == 2'b %s && insn_opcode == 2'b 01" % (funct6, funct2))
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1_rd")
        assign(f, "rvfi_spec_o.rs2_addr", "insn_rs2")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rs1_rd")
        if wmode:
            assign(f, "rvfi_spec_o.rd_wdata", "{{`RISCV_FORMAL_XLEN-32{result[31]}}, result}")
        else:
            assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")

        footer(f)

@gencheck
def insn_c_b(insn, funct3, expr, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_cb(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire cond = %s;" % expr, file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] next_pc = cond ? rvfi_i.pc_rdata + insn_imm : rvfi_i.pc_rdata + 2;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 01" % funct3)
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1")
        assign(f, "rvfi_spec_o.pc_wdata", "next_pc")
        assign(f, "rvfi_spec_o.trap", "(next_pc[0] != 0) || !misa_ok")

        footer(f)

@gencheck
def insn_c_sli(insn, expr, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci_sli(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] result = %s;" % expr, file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b 000 && insn_opcode == 2'b 10 && (!insn_shamt[5] || `RISCV_FORMAL_XLEN == 64)")
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1_rd")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rs1_rd")
        assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")

        footer(f)

@gencheck
def insn_c_lsp(insn, funct3, numbytes, signext, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_ci_lsp(f, numbytes)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("`ifdef RISCV_FORMAL_ALIGNED_MEM", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_i.rs1_rdata + insn_imm;", file=f)
        print("  wire [%d:0] result = rvfi_i.mem_rdata >> (8*(addr-rvfi_spec_o.mem_addr));" % (8*numbytes-1), file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 10 && insn_rd" % funct3)
        assign(f, "rvfi_spec_o.rs1_addr", "2")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        assign(f, "rvfi_spec_o.mem_addr", "addr & ~(`RISCV_FORMAL_XLEN/8-1)")
        assign(f, "rvfi_spec_o.mem_rmask", "((1 << %d)-1) << (addr-rvfi_spec_o.mem_addr)" % numbytes)
        if signext:
            assign(f, "rvfi_spec_o.rd_wdata", "$signed(result)")
        else:
            assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")
        assign(f, "rvfi_spec_o.trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`else", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_i.rs1_rdata + insn_imm;", file=f)
        print("  wire [%d:0] result = rvfi_i.mem_rdata;" % (8*numbytes-1), file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 10 && insn_rd" % funct3)
        assign(f, "rvfi_spec_o.rs1_addr", "2")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rd")
        assign(f, "rvfi_spec_o.mem_addr", "addr")
        assign(f, "rvfi_spec_o.mem_rmask", "((1 << %d)-1)" % numbytes)
        if signext:
            assign(f, "rvfi_spec_o.rd_wdata", "$signed(result)")
        else:
            assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")
        assign(f, "rvfi_spec_o.trap", "!misa_ok")

        print("`endif", file=f)

        footer(f)

@gencheck
def insn_c_ssp(insn, funct3, numbytes, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_css(f, numbytes)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("`ifdef RISCV_FORMAL_ALIGNED_MEM", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_i.rs1_rdata + insn_imm;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 10" % funct3)
        assign(f, "rvfi_spec_o.rs1_addr", "2")
        assign(f, "rvfi_spec_o.rs2_addr", "insn_rs2")
        assign(f, "rvfi_spec_o.mem_addr", "addr & ~(`RISCV_FORMAL_XLEN/8-1)")
        assign(f, "rvfi_spec_o.mem_wmask", "((1 << %d)-1) << (addr-rvfi_spec_o.mem_addr)" % numbytes)
        assign(f, "rvfi_spec_o.mem_wdata", "rvfi_i.rs2_rdata << (8*(addr-rvfi_spec_o.mem_addr))")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")
        assign(f, "rvfi_spec_o.trap", "((addr & (%d-1)) != 0) || !misa_ok" % numbytes)

        print("`else", file=f)

        print("  wire [`RISCV_FORMAL_XLEN-1:0] addr = rvfi_i.rs1_rdata + insn_imm;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct3 == 3'b %s && insn_opcode == 2'b 10" % funct3)
        assign(f, "rvfi_spec_o.rs1_addr", "2")
        assign(f, "rvfi_spec_o.rs2_addr", "insn_rs2")
        assign(f, "rvfi_spec_o.mem_addr", "addr")
        assign(f, "rvfi_spec_o.mem_wmask", "((1 << %d)-1)" % numbytes)
        assign(f, "rvfi_spec_o.mem_wdata", "rvfi_i.rs2_rdata")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")
        assign(f, "rvfi_spec_o.trap", "!misa_ok")

        print("`endif", file=f)

        footer(f)

@gencheck
def insn_c_jalr(insn, funct4, link, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_cr(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        print("  wire [`RISCV_FORMAL_XLEN-1:0] next_pc = rvfi_i.rs1_rdata & ~1;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct4 == 4'b %s && insn_rs1_rd && !insn_rs2 && insn_opcode == 2'b 10" % funct4)
        assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1_rd")
        if link:
            assign(f, "rvfi_spec_o.rd_addr", "5'd 1")
            assign(f, "rvfi_spec_o.rd_wdata", "rvfi_i.pc_rdata + 2")
        assign(f, "rvfi_spec_o.pc_wdata", "next_pc")
        assign(f, "rvfi_spec_o.trap", "(next_pc[0] != 0) || !misa_ok")

        footer(f)

@gencheck
def insn_c_mvadd(insn, funct4, add, misa=MISA_C):
    with open("insn_%s.v" % insn, "w") as f:
        header(f, insn)
        format_cr(f)
        misa_check(f, misa)

        print("", file=f)
        print("  // %s instruction" % insn.upper(), file=f)
        if add:
            print("  wire [`RISCV_FORMAL_XLEN-1:0] result = rvfi_i.rs1_rdata + rvfi_i.rs2_rdata;", file=f)
        else:
            print("  wire [`RISCV_FORMAL_XLEN-1:0] result = rvfi_i.rs2_rdata;", file=f)
        assign(f, "rvfi_spec_o.valid", "rvfi_i.valid && !insn_padding && insn_funct4 == 4'b %s && insn_rs2 && insn_opcode == 2'b 10" % funct4)
        if add:
            assign(f, "rvfi_spec_o.rs1_addr", "insn_rs1_rd")
        assign(f, "rvfi_spec_o.rs2_addr", "insn_rs2")
        assign(f, "rvfi_spec_o.rd_addr", "insn_rs1_rd")
        assign(f, "rvfi_spec_o.rd_wdata", "result")
        assign(f, "rvfi_spec_o.pc_wdata", "rvfi_i.pc_rdata + 2")

        footer(f)

## Base Integer ISA (I)

current_isa = ["rv32i"]

insn_lui()
insn_auipc()
insn_jal()
insn_jalr()

insn_b("beq",  "000", "rvfi_i.rs1_rdata == rvfi_i.rs2_rdata")
insn_b("bne",  "001", "rvfi_i.rs1_rdata != rvfi_i.rs2_rdata")
insn_b("blt",  "100", "$signed(rvfi_i.rs1_rdata) < $signed(rvfi_i.rs2_rdata)")
insn_b("bge",  "101", "$signed(rvfi_i.rs1_rdata) >= $signed(rvfi_i.rs2_rdata)")
insn_b("bltu", "110", "rvfi_i.rs1_rdata < rvfi_i.rs2_rdata")
insn_b("bgeu", "111", "rvfi_i.rs1_rdata >= rvfi_i.rs2_rdata")

insn_l("lb",  "000", 1, True)
insn_l("lh",  "001", 2, True)
insn_l("lw",  "010", 4, True)
insn_l("lbu", "100", 1, False)
insn_l("lhu", "101", 2, False)

insn_s("sb",  "000", 1)
insn_s("sh",  "001", 2)
insn_s("sw",  "010", 4)

insn_imm("addi",  "000", "rvfi_i.rs1_rdata + insn_imm")
insn_imm("slti",  "010", "$signed(rvfi_i.rs1_rdata) < $signed(insn_imm)")
insn_imm("sltiu", "011", "rvfi_i.rs1_rdata < insn_imm")
insn_imm("xori",  "100", "rvfi_i.rs1_rdata ^ insn_imm")
insn_imm("ori",   "110", "rvfi_i.rs1_rdata | insn_imm")
insn_imm("andi",  "111", "rvfi_i.rs1_rdata & insn_imm")

insn_shimm("slli", "000000", "001", "rvfi_i.rs1_rdata << insn_shamt")
insn_shimm("srli", "000000", "101", "rvfi_i.rs1_rdata >> insn_shamt")
insn_shimm("srai", "010000", "101", "$signed(rvfi_i.rs1_rdata) >>> insn_shamt")

insn_alu("add",  "0000000", "000", "rvfi_i.rs1_rdata + rvfi_i.rs2_rdata")
insn_alu("sub",  "0100000", "000", "rvfi_i.rs1_rdata - rvfi_i.rs2_rdata")
insn_alu("sll",  "0000000", "001", "rvfi_i.rs1_rdata << shamt", shamt=True)
insn_alu("slt",  "0000000", "010", "$signed(rvfi_i.rs1_rdata) < $signed(rvfi_i.rs2_rdata)")
insn_alu("sltu", "0000000", "011", "rvfi_i.rs1_rdata < rvfi_i.rs2_rdata")
insn_alu("xor",  "0000000", "100", "rvfi_i.rs1_rdata ^ rvfi_i.rs2_rdata")
insn_alu("srl",  "0000000", "101", "rvfi_i.rs1_rdata >> shamt", shamt=True)
insn_alu("sra",  "0100000", "101", "$signed(rvfi_i.rs1_rdata) >>> shamt", shamt=True)
insn_alu("or",   "0000000", "110", "rvfi_i.rs1_rdata | rvfi_i.rs2_rdata")
insn_alu("and",  "0000000", "111", "rvfi_i.rs1_rdata & rvfi_i.rs2_rdata")

current_isa = ["rv64i"]

insn_l("lwu", "110", 4, False)
insn_l("ld",  "011", 8, True)
insn_s("sd",  "011", 8)

insn_imm("addiw",  "000", "rvfi_i.rs1_rdata[31:0] + insn_imm[31:0]", wmode=True)

insn_shimm("slliw", "000000", "001", "rvfi_i.rs1_rdata[31:0] << insn_shamt", wmode=True)
insn_shimm("srliw", "000000", "101", "rvfi_i.rs1_rdata[31:0] >> insn_shamt", wmode=True)
insn_shimm("sraiw", "010000", "101", "$signed(rvfi_i.rs1_rdata[31:0]) >>> insn_shamt", wmode=True)

insn_alu("addw", "0000000", "000", "rvfi_i.rs1_rdata[31:0] + rvfi_i.rs2_rdata[31:0]", wmode=True)
insn_alu("subw", "0100000", "000", "rvfi_i.rs1_rdata[31:0] - rvfi_i.rs2_rdata[31:0]", wmode=True)
insn_alu("sllw", "0000000", "001", "rvfi_i.rs1_rdata[31:0] << shamt", shamt=True, wmode=True)
insn_alu("srlw", "0000000", "101", "rvfi_i.rs1_rdata[31:0] >> shamt", shamt=True, wmode=True)
insn_alu("sraw", "0100000", "101", "$signed(rvfi_i.rs1_rdata[31:0]) >>> shamt", shamt=True, wmode=True)

## Multiply/Divide ISA (M)

current_isa = ["rv32im"]

insn_alu("mul",    "0000001", "000", "rvfi_i.rs1_rdata * rvfi_i.rs2_rdata", alt_add=0x2cdf52a55876063e, misa=MISA_M)
insn_alu("mulh",   "0000001", "001", "({{`RISCV_FORMAL_XLEN{rvfi_i.rs1_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_i.rs1_rdata} *\n" +
        "\t\t{{`RISCV_FORMAL_XLEN{rvfi_i.rs2_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_i.rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_add=0x15d01651f6583fb7, misa=MISA_M)
insn_alu("mulhsu", "0000001", "010", "({{`RISCV_FORMAL_XLEN{rvfi_i.rs1_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_i.rs1_rdata} *\n" +
        "\t\t{`RISCV_FORMAL_XLEN'b0, rvfi_i.rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_sub=0xea3969edecfbe137, misa=MISA_M)
insn_alu("mulhu",  "0000001", "011", "({`RISCV_FORMAL_XLEN'b0, rvfi_i.rs1_rdata} * {`RISCV_FORMAL_XLEN'b0, rvfi_i.rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_add=0xd13db50d949ce5e8, misa=MISA_M)

insn_alu("div",    "0000001", "100", """rvfi_i.rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? {`RISCV_FORMAL_XLEN{1'b1}} :
                                         rvfi_i.rs1_rdata == {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} && rvfi_i.rs2_rdata == {`RISCV_FORMAL_XLEN{1'b1}} ? {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} :
                                         $signed(rvfi_i.rs1_rdata) / $signed(rvfi_i.rs2_rdata)""", alt_sub=0x29bbf66f7f8529ec, misa=MISA_M)

insn_alu("divu",   "0000001", "101", """rvfi_i.rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? {`RISCV_FORMAL_XLEN{1'b1}} :
                                         rvfi_i.rs1_rdata / rvfi_i.rs2_rdata""", alt_sub=0x8c629acb10e8fd70, misa=MISA_M)

insn_alu("rem",    "0000001", "110", """rvfi_i.rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? rvfi_i.rs1_rdata :
                                         rvfi_i.rs1_rdata == {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} && rvfi_i.rs2_rdata == {`RISCV_FORMAL_XLEN{1'b1}} ? {`RISCV_FORMAL_XLEN{1'b0}} :
                                         $signed(rvfi_i.rs1_rdata) % $signed(rvfi_i.rs2_rdata)""", alt_sub=0xf5b7d8538da68fa5, misa=MISA_M)

insn_alu("remu",   "0000001", "111", """rvfi_i.rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? rvfi_i.rs1_rdata :
                                         rvfi_i.rs1_rdata % rvfi_i.rs2_rdata""", alt_sub=0xbc4402413138d0e1, misa=MISA_M)

current_isa = ["rv64im"]

insn_alu("mulw",    "0000001", "000", "rvfi_i.rs1_rdata[31:0] * rvfi_i.rs2_rdata[31:0]", alt_add=0x2cdf52a55876063e, wmode=True, misa=MISA_M)

insn_alu("divw",    "0000001", "100", """rvfi_i.rs2_rdata[31:0] == 32'b0 ? {32{1'b1}} :
                       rvfi_i.rs1_rdata == {1'b1, {31{1'b0}}} && rvfi_i.rs2_rdata == {32{1'b1}} ? {1'b1, {31{1'b0}}} :
                       $signed(rvfi_i.rs1_rdata[31:0]) / $signed(rvfi_i.rs2_rdata[31:0])""", alt_sub=0x29bbf66f7f8529ec, wmode=True, misa=MISA_M)

insn_alu("divuw",   "0000001", "101", """rvfi_i.rs2_rdata[31:0] == 32'b0 ? {32{1'b1}} :
                       rvfi_i.rs1_rdata[31:0] / rvfi_i.rs2_rdata[31:0]""", alt_sub=0x8c629acb10e8fd70, wmode=True, misa=MISA_M)

insn_alu("remw",    "0000001", "110", """rvfi_i.rs2_rdata == 32'b0 ? rvfi_i.rs1_rdata :
                       rvfi_i.rs1_rdata == {1'b1, {31{1'b0}}} && rvfi_i.rs2_rdata == {32{1'b1}} ? {32{1'b0}} :
                       $signed(rvfi_i.rs1_rdata[31:0]) % $signed(rvfi_i.rs2_rdata[31:0])""", alt_sub=0xf5b7d8538da68fa5, wmode=True, misa=MISA_M)

insn_alu("remuw",   "0000001", "111", """rvfi_i.rs2_rdata == 32'b0 ? rvfi_i.rs1_rdata :
                       rvfi_i.rs1_rdata[31:0] % rvfi_i.rs2_rdata[31:0]""", alt_sub=0xbc4402413138d0e1, wmode=True, misa=MISA_M)

with open("insn_and_cover.tcl", "w+") as f:
    print(f"analyze +define+RISCV_FORMAL_INSN_MODEL=insn_and -f Flist.formal -sv insns/insn_and.v",file=f)
    print(f"elaborate -bbox_m {{wt_cache_subsystem wt_axi_adapter wt_dcache_mem sram}}",file=f)
    print(f"clock clk_i",file=f)
    print(f"reset !rst_ni",file=f)
    print(f"prove -all -cover ",file=f)
    print(f"load_radix_file radix.txt", file=f)
    print(f"report -results -file insns/insn_and.txt -force",file=f)
        
## ISA Propagate

def isa_propagate_pair(from_isa, to_isa):
     global isa_database
     assert from_isa in isa_database
     if to_isa not in isa_database:
         isa_database[to_isa] = set()
     isa_database[to_isa] |= isa_database[from_isa]

def isa_propagate(suffix):
    for i in range(2 ** len(suffix)):
        src = ""
        for k in range(len(suffix)):
            if ((i >> k) & 1) == 0:
                src += suffix[k]
        if src != suffix:
            isa_propagate_pair("rv32i"+src, "rv32i"+suffix)
            isa_propagate_pair("rv64i"+src, "rv64i"+suffix)
    isa_propagate_pair("rv32i"+suffix, "rv64i"+suffix)

isa_propagate("")
isa_propagate("c")
isa_propagate("m")
isa_propagate("mc")

## ISA Fixup

for isa, insns in isa_database.items():
    if isa.startswith("rv64"):
        insns.discard("c_jal")

## ISA Listings and ISA Models

for isa, insns in isa_database.items():
    with open("isa_%s.txt" % isa, "w") as f:
        for insn in sorted(insns):
            print(insn, file=f)

    with open("isa_%s.v" % isa, "w") as f:
        header(f, isa, isa_mode=True)

        for insn in sorted(insns):
            print("  wire                                rvfi_spec_o.insn_%s_valid;"     % insn, file=f)
            print("  wire                                rvfi_spec_o.insn_%s_trap;"      % insn, file=f)
            print("  wire [                       4 : 0] rvfi_spec_o.insn_%s_rs1_addr;"  % insn, file=f)
            print("  wire [                       4 : 0] rvfi_spec_o.insn_%s_rs2_addr;"  % insn, file=f)
            print("  wire [                       4 : 0] rvfi_spec_o.insn_%s_rd_addr;"   % insn, file=f)
            print("  wire [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_spec_o.insn_%s_rd_wdata;"  % insn, file=f)
            print("  wire [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_spec_o.insn_%s_pc_wdata;"  % insn, file=f)
            print("  wire [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_spec_o.insn_%s_mem_addr;"  % insn, file=f)
            print("  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] rvfi_spec_o.insn_%s_mem_rmask;" % insn, file=f)
            print("  wire [`RISCV_FORMAL_XLEN/8 - 1 : 0] rvfi_spec_o.insn_%s_mem_wmask;" % insn, file=f)
            print("  wire [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_spec_o.insn_%s_mem_wdata;"  % insn, file=f)
            print("`ifdef RISCV_FORMAL_CSR_MISA", file=f)
            print("  wire [`RISCV_FORMAL_XLEN   - 1 : 0] rvfi_spec_o.insn_%s_csr_misa_rmask;" % insn, file=f)
            print("`endif", file=f)
            print("", file=f)
            print("  rvfi_i.insn_%s insn_%s (" % (insn, insn), file=f)
            print("    .rvfi_i.valid(rvfi_i.valid),", file=f)
            print("    .rvfi_i.insn(rvfi_i.insn),", file=f)
            print("    .rvfi_i.pc_rdata(rvfi_i.pc_rdata),", file=f)
            print("    .rvfi_i.rs1_rdata(rvfi_i.rs1_rdata),", file=f)
            print("    .rvfi_i.rs2_rdata(rvfi_i.rs2_rdata),", file=f)
            print("    .rvfi_i.mem_rdata(rvfi_i.mem_rdata),", file=f)
            print("`ifdef RISCV_FORMAL_CSR_MISA", file=f)
            print("    .rvfi_i.csr_misa_rdata(rvfi_i.csr_misa_rdata),", file=f)
            print("    .rvfi_spec_o.csr_misa_rmask(rvfi_spec_o.insn_%s_csr_misa_rmask)," % insn, file=f)
            print("`endif", file=f)
            print("    .rvfi_spec_o.valid(rvfi_spec_o.insn_%s_valid)," % insn, file=f)
            print("    .rvfi_spec_o.trap(rvfi_spec_o.insn_%s_trap)," % insn, file=f)
            print("    .rvfi_spec_o.rs1_addr(rvfi_spec_o.insn_%s_rs1_addr)," % insn, file=f)
            print("    .rvfi_spec_o.rs2_addr(rvfi_spec_o.insn_%s_rs2_addr)," % insn, file=f)
            print("    .rvfi_spec_o.rd_addr(rvfi_spec_o.insn_%s_rd_addr)," % insn, file=f)
            print("    .rvfi_spec_o.rd_wdata(rvfi_spec_o.insn_%s_rd_wdata)," % insn, file=f)
            print("    .rvfi_spec_o.pc_wdata(rvfi_spec_o.insn_%s_pc_wdata)," % insn, file=f)
            print("    .rvfi_spec_o.mem_addr(rvfi_spec_o.insn_%s_mem_addr)," % insn, file=f)
            print("    .rvfi_spec_o.mem_rmask(rvfi_spec_o.insn_%s_mem_rmask)," % insn, file=f)
            print("    .rvfi_spec_o.mem_wmask(rvfi_spec_o.insn_%s_mem_wmask)," % insn, file=f)
            print("    .rvfi_spec_o.mem_wdata(rvfi_spec_o.insn_%s_mem_wdata)" % insn, file=f)
            print("  );", file=f)
            print("", file=f)

        for port in ["valid", "trap", "rs1_addr", "rs2_addr", "rd_addr", "rd_wdata", "pc_wdata", "mem_addr", "mem_rmask", "mem_wmask", "mem_wdata"]:
            print("  assign rvfi_spec_o.%s =\n\t\t%s : 0;" % (port, " :\n\t\t".join(["rvfi_spec_o.insn_%s_valid ? rvfi_spec_o.insn_%s_%s" % (insn, insn, port) for insn in sorted(insns)])), file=f)

        print("`ifdef RISCV_FORMAL_CSR_MISA", file=f)
        print("  assign rvfi_spec_o.csr_misa_rmask =\n\t\t%s : 0;" % (" :\n\t\t".join(["rvfi_spec_o.insn_%s_valid ? rvfi_spec_o.insn_%s_csr_misa_rmask" % (insn, insn) for insn in sorted(insns)])), file=f)
        print("`endif", file=f)

        print("endmodule", file=f)
