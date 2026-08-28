`timescale 1ns/1ps

module tb_oap_guardian_nexus_slice;
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic req_valid = 1'b0;
    logic req_consequential = 1'b0;
    logic [20:0] gate_pass = 21'h0;
    logic [31:0] nexus_payload_in = 32'h0;
    logic [255:0] hrm_hash_in = 256'h0;
    logic mmio_valid = 1'b0;
    logic mmio_write = 1'b0;
    logic [7:0] mmio_addr = 8'h0;
    logic [31:0] mmio_wdata = 32'h0;
    logic [31:0] mmio_rdata;
    logic mmio_ready;
    logic guardian_block;
    logic nexus_tx_valid;
    logic [31:0] nexus_payload_out;
    logic hrm_receipt_valid;
    logic [255:0] hrm_hash_out;
    logic irq_guardian;
    logic irq_nexus;
    logic irq_hrm;

    localparam logic [7:0] REG_STATUS      = 8'h00;
    localparam logic [7:0] REG_NEXUS_TX    = 8'h10;
    localparam logic [7:0] REG_NEXUS_COUNT = 8'h14;
    localparam logic [7:0] REG_HRM_COUNT   = 8'h18;
    localparam logic [7:0] REG_HRM_HASH0   = 8'h20;
    localparam logic [7:0] REG_IRQ_STATUS  = 8'h40;
    localparam logic [7:0] REG_IRQ_ACK     = 8'h44;

    oap_guardian_nexus_slice dut (
        .clk(clk),
        .rst_n(rst_n),
        .req_valid(req_valid),
        .req_consequential(req_consequential),
        .gate_pass(gate_pass),
        .nexus_payload_in(nexus_payload_in),
        .hrm_hash_in(hrm_hash_in),
        .mmio_valid(mmio_valid),
        .mmio_write(mmio_write),
        .mmio_addr(mmio_addr),
        .mmio_wdata(mmio_wdata),
        .mmio_rdata(mmio_rdata),
        .mmio_ready(mmio_ready),
        .guardian_block(guardian_block),
        .nexus_tx_valid(nexus_tx_valid),
        .nexus_payload_out(nexus_payload_out),
        .hrm_receipt_valid(hrm_receipt_valid),
        .hrm_hash_out(hrm_hash_out),
        .irq_guardian(irq_guardian),
        .irq_nexus(irq_nexus),
        .irq_hrm(irq_hrm)
    );

    always #5 clk = ~clk;

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

    task automatic pulse_request(
        input logic consequential,
        input logic [20:0] gates,
        input logic [31:0] payload,
        input logic [255:0] receipt_hash
    );
        begin
            @(negedge clk);
            req_consequential = consequential;
            gate_pass = gates;
            nexus_payload_in = payload;
            hrm_hash_in = receipt_hash;
            req_valid = 1'b1;
            @(posedge clk);
            #1;
            req_valid = 1'b0;
        end
    endtask

    logic [31:0] value;
    logic [255:0] known_hash;

    initial begin
        known_hash = 256'h0123456789abcdef_fedcba9876543210_0011223344556677_8899aabbccddeeff;

        repeat (2) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);
        #1;

        // Constitutional status must be immutable: Guardian on, Human Authority
        // final, and no real execution line enabled.
        mmio_read(REG_STATUS, value);
        if (value[0] !== 1'b1) $fatal(1, "Guardian must be enforcing");
        if (value[1] !== 1'b1) $fatal(1, "Human Authority must remain final");
        if (value[2] !== 1'b0) $fatal(1, "Real execution must remain disabled");

        // A consequential request with 20/21 gates must fail closed.
        pulse_request(1'b1, 21'h1f_ffff & ~(21'h1 << 7), 32'hdead_beef, known_hash);
        if (guardian_block !== 1'b1) $fatal(1, "Incomplete gates must trigger Guardian block");
        if (irq_guardian !== 1'b1) $fatal(1, "Guardian interrupt must be pending");
        if (irq_hrm !== 1'b1) $fatal(1, "Blocked request must still create HRM receipt event");
        if (nexus_tx_valid !== 1'b0) $fatal(1, "Blocked consequential request must not reach NEXUS");

        mmio_read(REG_HRM_COUNT, value);
        if (value !== 32'd1) $fatal(1, "Blocked request must increment HRM receipt count");

        // Clear pending Guardian + HRM interrupts.
        mmio_write_word(REG_IRQ_ACK, 32'h0000_0006);
        if (irq_guardian !== 1'b0 || irq_hrm !== 1'b0) $fatal(1, "IRQ acknowledgement failed");

        // All 21 gates release only an internal NEXUS result and an HRM receipt.
        pulse_request(1'b1, 21'h1f_ffff, 32'h0a50_0001, known_hash);
        if (guardian_block !== 1'b0) $fatal(1, "21/21 gates should clear the prior block state");
        if (nexus_tx_valid !== 1'b1) $fatal(1, "Approved simulation must pulse internal NEXUS");
        if (nexus_payload_out !== 32'h0a50_0001) $fatal(1, "NEXUS payload mismatch");
        if (hrm_receipt_valid !== 1'b1) $fatal(1, "Approved simulation must create HRM receipt event");
        if (hrm_hash_out !== known_hash) $fatal(1, "HRM receipt hash mismatch");
        if (irq_nexus !== 1'b1 || irq_hrm !== 1'b1) $fatal(1, "NEXUS and HRM interrupts must be pending");

        mmio_read(REG_HRM_HASH0, value);
        if (value !== known_hash[31:0]) $fatal(1, "HRM hash MMIO window mismatch");
        mmio_read(REG_NEXUS_COUNT, value);
        if (value !== 32'd1) $fatal(1, "NEXUS count should be one after approved request");
        mmio_read(REG_HRM_COUNT, value);
        if (value !== 32'd2) $fatal(1, "HRM count should include blocked and approved requests");

        // A direct MMIO NEXUS write is internal-only and increments the count.
        mmio_write_word(REG_NEXUS_TX, 32'h1234_5678);
        if (nexus_payload_out !== 32'h1234_5678) $fatal(1, "MMIO NEXUS payload mismatch");
        mmio_read(REG_NEXUS_COUNT, value);
        if (value !== 32'd2) $fatal(1, "MMIO NEXUS write did not increment count");

        // Attempts to write protected status space must fail closed.
        mmio_write_word(REG_STATUS, 32'hffff_ffff);
        if (guardian_block !== 1'b1) $fatal(1, "Protected status write must latch Guardian block");
        if (irq_guardian !== 1'b1) $fatal(1, "Protected status write must raise Guardian interrupt");

        mmio_read(REG_IRQ_STATUS, value);
        if (value[2] !== 1'b1) $fatal(1, "Guardian IRQ status bit missing");

        $display("OAP_RTL_PROOF_SLICE_V0_PASS");
        $finish;
    end

endmodule
