// Copyright (C) 2017  Claire Xenia Wolf <claire@yosyshq.com>
//
// Permission to use, copy, modify, and/or distribute this software for any
// purpose with or without fee is hereby granted, provided that the above
// copyright notice and this permission notice appear in all copies.
//
// THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
// WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
// MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
// ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
// WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
// ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
// OR IN CONNECTION WITH THE USE OR P
import ariane_pkg::*;
module rvfi_insn_check (
	input clk_i, rst_ni, check,
	input ariane_rvfi_pkg::rvfi_port_t rvfi_i	
);

	logic [31:0] rvfi_spec_rs2_rdata,rvfi_spec_rs1_rdata;
	ariane_rvfi_pkg::rvfi_spec_port_t rvfi_spec;

	`RISCV_FORMAL_INSN_MODEL insn_spec (
		.rvfi_i,
		.rvfi_spec_o(rvfi_spec)
	);

	wire [1:0] mem_log2len =
		((rvfi_spec.mem_rmask | rvfi_spec.mem_wmask) & 8'b 1111_0000) ? 3 :
		((rvfi_spec.mem_rmask | rvfi_spec.mem_wmask) & 8'b 0000_1100) ? 2 :
		((rvfi_spec.mem_rmask | rvfi_spec.mem_wmask) & 8'b 0000_0010) ? 1 : 0;
	
	always @* begin
		if (rst_ni && check) begin
			spec_valid_assume: assume(rvfi_spec.valid);

			if (!`rvformal_addr_valid(rvfi_i.pc_rdata)) begin
				trap_prop: 			assert(rvfi_i.trap);
				trap_rd_addr_0_prop: assert(rvfi_i.rd_addr == 0);
				trap_rd_wdata_0_prop: assert(rvfi_i.rd_wdata == 0);
				trap_rd_wmask_0_prop: assert(rvfi_i.mem_wmask == 0);
			end else begin

				if (rvfi_i.rs1_addr == 0)
					rs1_addr_0_data_0_prop: assert(rvfi_i.rs1_rdata == 0);
				
				if (rvfi_i.rs2_addr == 0)
					rs2_addr_0_data_0_prop: assert(rvfi_i.rs2_rdata == 0);

				if (!rvfi_spec.trap) begin

					if (rvfi_spec.rs1_addr != 0) begin
						rs1_addr_match_prop: assert(rvfi_spec.rs1_addr == rvfi_i.rs1_addr);
					end

					if (rvfi_spec.rs2_addr != 0) begin
						rs2_addr_match_prop: assert(rvfi_spec.rs2_addr == rvfi_i.rs2_addr);
					end

					rd_addr_match_prop: assert(rvfi_spec.rd_addr == rvfi_i.rd_addr);
					rd_wdata_match_prop: assert(rvfi_spec.rd_wdata == rvfi_i.rd_wdata);
					pc_wdata_match_prop: assert(`rvformal_addr_eq(rvfi_spec.pc_wdata, rvfi_i.pc_wdata));

					if (rvfi_spec.mem_wmask || rvfi_spec.mem_rmask) begin
						mem_addr_match_prop: assert(`rvformal_addr_eq(rvfi_spec.mem_addr, rvfi_i.mem_addr));
						mem_wdata_match_prop: assert(rvfi_spec.mem_wdata == rvfi_i.mem_wdata);
					end
				end
				trap_match_prop: assert(rvfi_spec.trap == rvfi_i.trap);
			end
		end
		if (rst_ni) begin
			spec_valid_cover: cover(check && rvfi_spec.valid);
			rs1_addr_0_cover: cover(rvfi_i.rs1_addr == '0);
			rs1_addr_not_0_cover: cover(rvfi_i.rs1_addr != '0);
			rs1_data_not_0_cover: cover(rvfi_i.rs1_rdata != '0);
		end
	end
endmodule
