// OAP RTL Proof Slice v0
//
// First hardware-description proof for the OAP Sovereign Digital SoC.
// This module models a Guardian policy boundary, NEXUS MMIO transmit path,
// prioritised interrupt state and HRM receipt/hash registers. It performs no
// external or physical execution. SMI remains the single Brain and Human
// Authority remains final above this hardware layer.

module oap_guardian_nexus_slice (
    input  logic         clk,
    input  logic         rst_n,

    input  logic         req_valid,
    input  logic         req_consequential,
    input  logic [20:0]  gate_pass,
    input  logic [31:0]  nexus_payload_in,
    input  logic [255:0] hrm_hash_in,

    input  logic         mmio_valid,
    input  logic         mmio_write,
    input  logic [7:0]   mmio_addr,
    input  logic [31:0]  mmio_wdata,
    output logic [31:0]  mmio_rdata,
    output logic         mmio_ready,

    output logic         guardian_block,
    output logic         nexus_tx_valid,
    output logic [31:0]  nexus_payload_out,
    output logic         hrm_receipt_valid,
    output logic [255:0] hrm_hash_out,
    output logic         irq_guardian,
    output logic         irq_nexus,
    output logic         irq_hrm
);

    localparam logic [7:0] REG_STATUS       = 8'h00;
    localparam logic [7:0] REG_GATE_STATUS  = 8'h04;
    localparam logic [7:0] REG_NEXUS_TX     = 8'h10;
    localparam logic [7:0] REG_NEXUS_COUNT  = 8'h14;
    localparam logic [7:0] REG_HRM_COUNT    = 8'h18;
    localparam logic [7:0] REG_HRM_HASH0    = 8'h20;
    localparam logic [7:0] REG_HRM_HASH1    = 8'h24;
    localparam logic [7:0] REG_HRM_HASH2    = 8'h28;
    localparam logic [7:0] REG_HRM_HASH3    = 8'h2c;
    localparam logic [7:0] REG_HRM_HASH4    = 8'h30;
    localparam logic [7:0] REG_HRM_HASH5    = 8'h34;
    localparam logic [7:0] REG_HRM_HASH6    = 8'h38;
    localparam logic [7:0] REG_HRM_HASH7    = 8'h3c;
    localparam logic [7:0] REG_IRQ_STATUS   = 8'h40;
    localparam logic [7:0] REG_IRQ_ACK      = 8'h44;

    // irq_pending bit order is deliberately explicit:
    // [2] Guardian, [1] HRM, [0] NEXUS.
    logic [2:0] irq_pending;
    logic [31:0] nexus_tx_count;
    logic [31:0] hrm_receipt_count;

    wire all_21_gates_pass = &gate_pass;

    assign irq_guardian = irq_pending[2];
    assign irq_hrm      = irq_pending[1];
    assign irq_nexus    = irq_pending[0];
    assign mmio_ready   = mmio_valid;

    always_comb begin
        mmio_rdata = 32'h0000_0000;
        unique case (mmio_addr)
            REG_STATUS: begin
                // bit 0: Guardian enforcing (always 1)
                // bit 1: Human Authority final (always 1)
                // bit 2: real execution enabled (always 0)
                // bit 3: last request blocked
                mmio_rdata = {28'h0, guardian_block, 1'b0, 1'b1, 1'b1};
            end
            REG_GATE_STATUS: mmio_rdata = {11'h000, gate_pass};
            REG_NEXUS_COUNT: mmio_rdata = nexus_tx_count;
            REG_HRM_COUNT:   mmio_rdata = hrm_receipt_count;
            REG_HRM_HASH0:   mmio_rdata = hrm_hash_out[31:0];
            REG_HRM_HASH1:   mmio_rdata = hrm_hash_out[63:32];
            REG_HRM_HASH2:   mmio_rdata = hrm_hash_out[95:64];
            REG_HRM_HASH3:   mmio_rdata = hrm_hash_out[127:96];
            REG_HRM_HASH4:   mmio_rdata = hrm_hash_out[159:128];
            REG_HRM_HASH5:   mmio_rdata = hrm_hash_out[191:160];
            REG_HRM_HASH6:   mmio_rdata = hrm_hash_out[223:192];
            REG_HRM_HASH7:   mmio_rdata = hrm_hash_out[255:224];
            REG_IRQ_STATUS:  mmio_rdata = {29'h0, irq_pending};
            default:         mmio_rdata = 32'h0000_0000;
        endcase
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            guardian_block   <= 1'b0;
            nexus_tx_valid   <= 1'b0;
            nexus_payload_out <= 32'h0000_0000;
            hrm_receipt_valid <= 1'b0;
            hrm_hash_out     <= 256'h0;
            irq_pending      <= 3'b000;
            nexus_tx_count   <= 32'h0000_0000;
            hrm_receipt_count <= 32'h0000_0000;
        end else begin
            nexus_tx_valid    <= 1'b0;
            hrm_receipt_valid <= 1'b0;

            // Explicit interrupt acknowledgement. A same-cycle new event below
            // wins over acknowledgement and remains pending.
            if (mmio_valid && mmio_write && mmio_addr == REG_IRQ_ACK) begin
                irq_pending <= irq_pending & ~mmio_wdata[2:0];
            end

            // Writes to protected/read-only control space fail closed.
            if (mmio_valid && mmio_write &&
                (mmio_addr == REG_STATUS ||
                 mmio_addr == REG_GATE_STATUS ||
                 mmio_addr == REG_NEXUS_COUNT ||
                 mmio_addr == REG_HRM_COUNT ||
                 (mmio_addr >= REG_HRM_HASH0 && mmio_addr <= REG_HRM_HASH7) ||
                 mmio_addr == REG_IRQ_STATUS)) begin
                guardian_block <= 1'b1;
                irq_pending[2] <= 1'b1;
            end

            // NEXUS MMIO is an internal message path only. It does not expose an
            // external execution line.
            if (mmio_valid && mmio_write && mmio_addr == REG_NEXUS_TX) begin
                nexus_payload_out <= mmio_wdata;
                nexus_tx_valid <= 1'b1;
                nexus_tx_count <= nexus_tx_count + 1'b1;
                irq_pending[0] <= 1'b1;
            end

            // Consequential requests fail closed unless all 21 gates are true.
            // A passing request is only released to the internal NEXUS path;
            // this proof slice has no real-world execution output.
            if (req_valid) begin
                hrm_hash_out <= hrm_hash_in;
                hrm_receipt_valid <= 1'b1;
                hrm_receipt_count <= hrm_receipt_count + 1'b1;
                irq_pending[1] <= 1'b1;

                if (req_consequential && !all_21_gates_pass) begin
                    guardian_block <= 1'b1;
                    irq_pending[2] <= 1'b1;
                end else begin
                    guardian_block <= 1'b0;
                    nexus_payload_out <= nexus_payload_in;
                    nexus_tx_valid <= 1'b1;
                    nexus_tx_count <= nexus_tx_count + 1'b1;
                    irq_pending[0] <= 1'b1;
                end
            end
        end
    end

endmodule
