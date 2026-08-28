`timescale 1ns/1ps

// OAP RTL Trust / Attestation Core v0
//
// Simulation-first hardware-description proof for immutable measured-boot
// evidence, one-time HRM integrity linkage, nonce/challenge handling and
// Guardian-bound attestation failure. This block performs no cryptographic
// signing, key provisioning, external execution or hardware-backed attestation.
// SMI remains the single Brain and Human Authority remains final above RTL.

module oap_trust_attestation_core (
    input  logic         clk,
    input  logic         rst_n,

    input  logic         measurement_valid,
    input  logic [1:0]   measurement_slot,
    input  logic [255:0] measurement_digest_in,

    input  logic         hrm_link_valid,
    input  logic [255:0] hrm_link_digest_in,

    input  logic         challenge_valid,
    input  logic [127:0] nonce_in,

    input  logic         mmio_valid,
    input  logic         mmio_write,
    input  logic [7:0]   mmio_addr,
    input  logic [31:0]  mmio_wdata,
    output logic [31:0]  mmio_rdata,
    output logic         mmio_ready,

    output logic         guardian_block,
    output logic         attestation_ready,
    output logic         attestation_valid,
    output logic [255:0] attestation_proof,
    output logic         irq_guardian,
    output logic         irq_attestation,
    output logic [2:0]   measurement_count,
    output logic [31:0]  violation_count
);

    localparam logic [7:0] REG_STATUS        = 8'h00;
    localparam logic [7:0] REG_MEAS_COUNT    = 8'h04;
    localparam logic [7:0] REG_WRITTEN       = 8'h08;
    localparam logic [7:0] REG_VIOL_COUNT    = 8'h0c;
    localparam logic [7:0] REG_CHAIN0        = 8'h10;
    localparam logic [7:0] REG_CHAIN7        = 8'h2c;
    localparam logic [7:0] REG_ATTEST0       = 8'h30;
    localparam logic [7:0] REG_ATTEST7       = 8'h4c;
    localparam logic [7:0] REG_NONCE0        = 8'h50;
    localparam logic [7:0] REG_NONCE3        = 8'h5c;
    localparam logic [7:0] REG_IRQ_STATUS    = 8'h60;
    localparam logic [7:0] REG_ATTEST_COUNT  = 8'h64;
    localparam logic [7:0] REG_IRQ_ACK       = 8'h68;

    logic [255:0] measurements [0:3];
    logic [3:0] written_bitmap;
    logic [255:0] chain_state;
    logic [255:0] hrm_link_digest;
    logic hrm_linked;
    logic [127:0] last_nonce;
    logic last_nonce_valid;
    logic [1:0] irq_pending;
    logic [31:0] attestation_count;

    wire all_measurements_present = &written_bitmap;
    wire [255:0] nonce_expanded = {nonce_in, nonce_in};

    assign irq_guardian = irq_pending[1];
    assign irq_attestation = irq_pending[0];
    assign attestation_ready = all_measurements_present && hrm_linked && !guardian_block;
    assign mmio_ready = mmio_valid;

    function automatic [31:0] word256(
        input logic [255:0] value,
        input logic [2:0] index
    );
        begin
            case (index)
                3'd0: word256 = value[31:0];
                3'd1: word256 = value[63:32];
                3'd2: word256 = value[95:64];
                3'd3: word256 = value[127:96];
                3'd4: word256 = value[159:128];
                3'd5: word256 = value[191:160];
                3'd6: word256 = value[223:192];
                default: word256 = value[255:224];
            endcase
        end
    endfunction

    always @* begin
        mmio_rdata = 32'h0000_0000;
        case (mmio_addr)
            REG_STATUS: begin
                // bit 0: trust/Guardian enforcement active (always 1)
                // bit 1: Human Authority final (always 1)
                // bit 2: hardware-backed attestation (always 0 in v0)
                // bit 3: Guardian block latched
                // bit 4: attestation ready
                // bit 5: attestation-valid pulse state
                // bit 6: HRM integrity link sealed
                // bit 7: all required boot measurements sealed
                mmio_rdata = {
                    24'h0,
                    all_measurements_present,
                    hrm_linked,
                    attestation_valid,
                    attestation_ready,
                    guardian_block,
                    1'b0,
                    1'b1,
                    1'b1
                };
            end
            REG_MEAS_COUNT:   mmio_rdata = {29'h0, measurement_count};
            REG_WRITTEN:      mmio_rdata = {28'h0, written_bitmap};
            REG_VIOL_COUNT:   mmio_rdata = violation_count;
            REG_CHAIN0,
            8'h14,
            8'h18,
            8'h1c,
            8'h20,
            8'h24,
            8'h28,
            REG_CHAIN7:       mmio_rdata = word256(chain_state, (mmio_addr - REG_CHAIN0) >> 2);
            REG_ATTEST0,
            8'h34,
            8'h38,
            8'h3c,
            8'h40,
            8'h44,
            8'h48,
            REG_ATTEST7:      mmio_rdata = word256(attestation_proof, (mmio_addr - REG_ATTEST0) >> 2);
            REG_NONCE0:       mmio_rdata = last_nonce[31:0];
            8'h54:            mmio_rdata = last_nonce[63:32];
            8'h58:            mmio_rdata = last_nonce[95:64];
            REG_NONCE3:       mmio_rdata = last_nonce[127:96];
            REG_IRQ_STATUS:   mmio_rdata = {30'h0, irq_pending};
            REG_ATTEST_COUNT: mmio_rdata = attestation_count;
            default:          mmio_rdata = 32'h0000_0000;
        endcase
    end

    integer i;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 4; i = i + 1) begin
                measurements[i] <= 256'h0;
            end
            written_bitmap     <= 4'b0000;
            measurement_count  <= 3'd0;
            chain_state        <= 256'h0;
            hrm_link_digest    <= 256'h0;
            hrm_linked         <= 1'b0;
            last_nonce         <= 128'h0;
            last_nonce_valid   <= 1'b0;
            guardian_block     <= 1'b0;
            attestation_valid  <= 1'b0;
            attestation_proof  <= 256'h0;
            irq_pending        <= 2'b00;
            violation_count    <= 32'h0;
            attestation_count  <= 32'h0;
        end else begin
            attestation_valid <= 1'b0;

            // Interrupt acknowledgement is the only writable MMIO control.
            if (mmio_valid && mmio_write && mmio_addr == REG_IRQ_ACK) begin
                irq_pending <= irq_pending & ~mmio_wdata[1:0];
            end

            // All other MMIO writes target protected trust state and fail closed.
            if (mmio_valid && mmio_write && mmio_addr != REG_IRQ_ACK) begin
                guardian_block  <= 1'b1;
                irq_pending[1]  <= 1'b1;
                violation_count <= violation_count + 1'b1;
            end

            // Four boot measurement slots are write-once until reset. The chain
            // is an integrity-path proof mixer, not a cryptographic hash engine.
            if (measurement_valid) begin
                if (written_bitmap[measurement_slot]) begin
                    guardian_block  <= 1'b1;
                    irq_pending[1]  <= 1'b1;
                    violation_count <= violation_count + 1'b1;
                end else begin
                    measurements[measurement_slot] <= measurement_digest_in;
                    written_bitmap[measurement_slot] <= 1'b1;
                    measurement_count <= measurement_count + 1'b1;
                    chain_state <= {
                        chain_state[127:0],
                        chain_state[255:128]
                    } ^ measurement_digest_in ^ {254'h0, measurement_slot};
                end
            end

            // HRM linkage is also write-once. This models a sealed integrity
            // relationship, not a physical fuse or key store.
            if (hrm_link_valid) begin
                if (hrm_linked) begin
                    guardian_block  <= 1'b1;
                    irq_pending[1]  <= 1'b1;
                    violation_count <= violation_count + 1'b1;
                end else begin
                    hrm_link_digest <= hrm_link_digest_in;
                    hrm_linked <= 1'b1;
                end
            end

            // A challenge is accepted only after all boot measurements and the
            // HRM link are sealed. Nonces are single-use within a reset epoch.
            if (challenge_valid) begin
                if (!all_measurements_present || !hrm_linked || guardian_block) begin
                    guardian_block  <= 1'b1;
                    irq_pending[1]  <= 1'b1;
                    violation_count <= violation_count + 1'b1;
                end else if (last_nonce_valid && nonce_in == last_nonce) begin
                    guardian_block  <= 1'b1;
                    irq_pending[1]  <= 1'b1;
                    violation_count <= violation_count + 1'b1;
                end else begin
                    last_nonce <= nonce_in;
                    last_nonce_valid <= 1'b1;
                    // Deterministic proof token for simulation only. It is not a
                    // signature and provides no cryptographic security claim.
                    attestation_proof <= chain_state ^ hrm_link_digest ^ nonce_expanded;
                    attestation_valid <= 1'b1;
                    attestation_count <= attestation_count + 1'b1;
                    irq_pending[0] <= 1'b1;
                end
            end
        end
    end

endmodule
