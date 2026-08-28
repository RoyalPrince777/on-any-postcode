`timescale 1ns/1ps

module tb_oap_trust_attestation_core;
    logic clk = 1'b0;
    logic rst_n = 1'b0;

    logic measurement_valid = 1'b0;
    logic [1:0] measurement_slot = 2'b00;
    logic [255:0] measurement_digest_in = 256'h0;
    logic hrm_link_valid = 1'b0;
    logic [255:0] hrm_link_digest_in = 256'h0;
    logic challenge_valid = 1'b0;
    logic [127:0] nonce_in = 128'h0;

    logic mmio_valid = 1'b0;
    logic mmio_write = 1'b0;
    logic [7:0] mmio_addr = 8'h0;
    logic [31:0] mmio_wdata = 32'h0;
    logic [31:0] mmio_rdata;
    logic mmio_ready;

    logic guardian_block;
    logic attestation_ready;
    logic attestation_valid;
    logic [255:0] attestation_proof;
    logic irq_guardian;
    logic irq_attestation;
    logic [2:0] measurement_count;
    logic [31:0] violation_count;

    localparam logic [7:0] REG_STATUS       = 8'h00;
    localparam logic [7:0] REG_MEAS_COUNT   = 8'h04;
    localparam logic [7:0] REG_WRITTEN      = 8'h08;
    localparam logic [7:0] REG_VIOL_COUNT   = 8'h0c;
    localparam logic [7:0] REG_CHAIN0       = 8'h10;
    localparam logic [7:0] REG_ATTEST0      = 8'h30;
    localparam logic [7:0] REG_NONCE0       = 8'h50;
    localparam logic [7:0] REG_IRQ_STATUS   = 8'h60;
    localparam logic [7:0] REG_ATTEST_COUNT = 8'h64;
    localparam logic [7:0] REG_IRQ_ACK      = 8'h68;

    oap_trust_attestation_core dut (
        .clk(clk),
        .rst_n(rst_n),
        .measurement_valid(measurement_valid),
        .measurement_slot(measurement_slot),
        .measurement_digest_in(measurement_digest_in),
        .hrm_link_valid(hrm_link_valid),
        .hrm_link_digest_in(hrm_link_digest_in),
        .challenge_valid(challenge_valid),
        .nonce_in(nonce_in),
        .mmio_valid(mmio_valid),
        .mmio_write(mmio_write),
        .mmio_addr(mmio_addr),
        .mmio_wdata(mmio_wdata),
        .mmio_rdata(mmio_rdata),
        .mmio_ready(mmio_ready),
        .guardian_block(guardian_block),
        .attestation_ready(attestation_ready),
        .attestation_valid(attestation_valid),
        .attestation_proof(attestation_proof),
        .irq_guardian(irq_guardian),
        .irq_attestation(irq_attestation),
        .measurement_count(measurement_count),
        .violation_count(violation_count)
    );

    always #5 clk = ~clk;

    task automatic reset_dut;
        begin
            rst_n = 1'b0;
            measurement_valid = 1'b0;
            hrm_link_valid = 1'b0;
            challenge_valid = 1'b0;
            mmio_valid = 1'b0;
            mmio_write = 1'b0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;
            @(posedge clk);
            #1;
        end
    endtask

    task automatic pulse_measure(
        input logic [1:0] slot,
        input logic [255:0] digest
    );
        begin
            @(negedge clk);
            measurement_slot = slot;
            measurement_digest_in = digest;
            measurement_valid = 1'b1;
            @(posedge clk);
            #1;
            measurement_valid = 1'b0;
        end
    endtask

    task automatic pulse_hrm(input logic [255:0] digest);
        begin
            @(negedge clk);
            hrm_link_digest_in = digest;
            hrm_link_valid = 1'b1;
            @(posedge clk);
            #1;
            hrm_link_valid = 1'b0;
        end
    endtask

    task automatic pulse_challenge(input logic [127:0] nonce);
        begin
            @(negedge clk);
            nonce_in = nonce;
            challenge_valid = 1'b1;
            @(posedge clk);
            #1;
            challenge_valid = 1'b0;
        end
    endtask

    task automatic mmio_read(input logic [7:0] addr, output logic [31:0] value);
        begin
            @(negedge clk);
            mmio_addr = addr;
            mmio_write = 1'b0;
            mmio_valid = 1'b1;
            #1;
            if (!mmio_ready) $fatal(1, "MMIO read did not become ready");
            value = mmio_rdata;
            @(negedge clk);
            mmio_valid = 1'b0;
            mmio_addr = 8'h0;
        end
    endtask

    task automatic mmio_write_word(input logic [7:0] addr, input logic [31:0] value);
        begin
            @(negedge clk);
            mmio_addr = addr;
            mmio_wdata = value;
            mmio_write = 1'b1;
            mmio_valid = 1'b1;
            @(posedge clk);
            #1;
            @(negedge clk);
            mmio_valid = 1'b0;
            mmio_write = 1'b0;
            mmio_addr = 8'h0;
            mmio_wdata = 32'h0;
        end
    endtask

    logic [31:0] value;
    logic [31:0] chain_word_before;
    logic [255:0] proof_snapshot;
    logic [127:0] nonce_a;

    initial begin
        nonce_a = 128'h1122334455667788_99aabbccddeeff00;

        // Constitutional status is immutable and explicitly not hardware-backed.
        reset_dut();
        mmio_read(REG_STATUS, value);
        if (value[0] !== 1'b1) $fatal(1, "Trust enforcement must be active");
        if (value[1] !== 1'b1) $fatal(1, "Human Authority must remain final");
        if (value[2] !== 1'b0) $fatal(1, "v0 must not claim hardware-backed attestation");

        // A challenge before measured boot + HRM linkage must fail closed.
        pulse_challenge(nonce_a);
        if (guardian_block !== 1'b1) $fatal(1, "Incomplete trust state must trigger Guardian block");
        if (irq_guardian !== 1'b1) $fatal(1, "Incomplete trust state must raise Guardian IRQ");
        if (attestation_valid !== 1'b0) $fatal(1, "Failed challenge must not produce attestation");
        if (violation_count !== 32'd1) $fatal(1, "Failed challenge must increment violation count");

        // Fresh epoch: seal four immutable measurements and one HRM integrity link.
        reset_dut();
        pulse_measure(2'd0, 256'h0001);
        pulse_measure(2'd1, 256'h0010);
        pulse_measure(2'd2, 256'h0100);
        pulse_measure(2'd3, 256'h1000);
        pulse_hrm(256'hfeed_face_cafe_beef_dead_beef_0123_4567_89ab_cdef_0011_2233_4455_6677_8899);

        if (measurement_count !== 3'd4) $fatal(1, "All four measured-boot slots must be sealed");
        if (!attestation_ready) $fatal(1, "Attestation should be ready after measurements + HRM linkage");
        mmio_read(REG_WRITTEN, value);
        if (value[3:0] !== 4'b1111) $fatal(1, "Measurement write-once bitmap mismatch");
        mmio_read(REG_MEAS_COUNT, value);
        if (value !== 32'd4) $fatal(1, "Measurement count MMIO mismatch");
        mmio_read(REG_CHAIN0, chain_word_before);
        if (chain_word_before === 32'h0) $fatal(1, "Measurement chain should not remain zero");

        // A fresh challenge produces only a deterministic simulation proof.
        pulse_challenge(nonce_a);
        if (guardian_block !== 1'b0) $fatal(1, "Valid trust state must not trigger Guardian block");
        if (attestation_valid !== 1'b1) $fatal(1, "Valid challenge must pulse attestation_valid");
        if (irq_attestation !== 1'b1) $fatal(1, "Attestation IRQ must be pending");
        proof_snapshot = attestation_proof;
        if (proof_snapshot === 256'h0) $fatal(1, "Simulation proof token should be populated");
        mmio_read(REG_ATTEST0, value);
        if (value !== proof_snapshot[31:0]) $fatal(1, "Attestation proof MMIO mismatch");
        mmio_read(REG_NONCE0, value);
        if (value !== nonce_a[31:0]) $fatal(1, "Nonce MMIO mismatch");
        mmio_read(REG_ATTEST_COUNT, value);
        if (value !== 32'd1) $fatal(1, "Attestation count should be one");

        // Replaying the same nonce in the same reset epoch fails closed.
        pulse_challenge(nonce_a);
        if (guardian_block !== 1'b1) $fatal(1, "Nonce replay must trigger Guardian block");
        if (irq_guardian !== 1'b1) $fatal(1, "Nonce replay must raise Guardian IRQ");
        if (attestation_valid !== 1'b0) $fatal(1, "Nonce replay must not create a second proof");
        if (violation_count !== 32'd1) $fatal(1, "Nonce replay must increment violation count");

        mmio_read(REG_IRQ_STATUS, value);
        if (value[1] !== 1'b1) $fatal(1, "Guardian IRQ status bit missing");

        // A measurement slot cannot be rewritten and the chain must stay stable.
        reset_dut();
        pulse_measure(2'd0, 256'h55aa);
        mmio_read(REG_CHAIN0, chain_word_before);
        pulse_measure(2'd0, 256'haa55);
        if (guardian_block !== 1'b1) $fatal(1, "Measurement rewrite must fail closed");
        mmio_read(REG_CHAIN0, value);
        if (value !== chain_word_before) $fatal(1, "Rejected measurement rewrite changed the chain");

        // Protected trust registers reject writes. IRQ_ACK remains the only
        // writable MMIO control and can clear the pending Guardian IRQ.
        reset_dut();
        mmio_write_word(REG_STATUS, 32'hffff_ffff);
        if (guardian_block !== 1'b1) $fatal(1, "Protected trust register write must fail closed");
        if (irq_guardian !== 1'b1) $fatal(1, "Protected write must raise Guardian IRQ");
        mmio_read(REG_VIOL_COUNT, value);
        if (value !== 32'd1) $fatal(1, "Protected write must increment violation count");
        mmio_write_word(REG_IRQ_ACK, 32'h0000_0002);
        if (irq_guardian !== 1'b0) $fatal(1, "Guardian IRQ acknowledgement failed");

        $display("OAP_RTL_ATTESTATION_V0_PASS");
        $finish;
    end

endmodule
