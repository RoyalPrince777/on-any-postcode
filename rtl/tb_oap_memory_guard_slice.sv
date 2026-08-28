`timescale 1ns/1ps

module tb_oap_memory_guard_slice;
    logic clk = 1'b0;
    logic rst_n = 1'b0;

    logic access_valid = 1'b0;
    logic access_write = 1'b0;
    logic [2:0] requester_zone = 3'd0;
    logic [31:0] access_addr = 32'h0;

    logic dma_valid = 1'b0;
    logic [6:0] dma_domain_mask = 7'h0;
    logic [31:0] dma_source_addr = 32'h0;
    logic [31:0] dma_target_addr = 32'h0;

    logic mmio_valid = 1'b0;
    logic mmio_write = 1'b0;
    logic [7:0] mmio_addr = 8'h0;
    logic [31:0] mmio_wdata = 32'h0;
    logic [31:0] mmio_rdata;
    logic mmio_ready;

    logic access_allow;
    logic access_block;
    logic [2:0] access_target_zone;
    logic dma_allow;
    logic dma_block;
    logic [2:0] dma_source_zone;
    logic [2:0] dma_target_zone;
    logic irq_guardian;
    logic [31:0] violation_count;

    localparam logic [2:0] Z_PUBLIC   = 3'd0;
    localparam logic [2:0] Z_PRIVATE  = 3'd1;
    localparam logic [2:0] Z_SMI      = 3'd2;
    localparam logic [2:0] Z_HRM      = 3'd3;
    localparam logic [2:0] Z_GUARDIAN = 3'd4;
    localparam logic [2:0] Z_DEVICE   = 3'd5;
    localparam logic [2:0] Z_RECOVERY = 3'd6;

    localparam logic [7:0] REG_STATUS     = 8'h00;
    localparam logic [7:0] REG_VIOLATIONS = 8'h04;
    localparam logic [7:0] REG_IRQ_STATUS = 8'h10;
    localparam logic [7:0] REG_IRQ_ACK    = 8'h14;

    oap_memory_guard_slice dut (
        .clk(clk),
        .rst_n(rst_n),
        .access_valid(access_valid),
        .access_write(access_write),
        .requester_zone(requester_zone),
        .access_addr(access_addr),
        .dma_valid(dma_valid),
        .dma_domain_mask(dma_domain_mask),
        .dma_source_addr(dma_source_addr),
        .dma_target_addr(dma_target_addr),
        .mmio_valid(mmio_valid),
        .mmio_write(mmio_write),
        .mmio_addr(mmio_addr),
        .mmio_wdata(mmio_wdata),
        .mmio_rdata(mmio_rdata),
        .mmio_ready(mmio_ready),
        .access_allow(access_allow),
        .access_block(access_block),
        .access_target_zone(access_target_zone),
        .dma_allow(dma_allow),
        .dma_block(dma_block),
        .dma_source_zone(dma_source_zone),
        .dma_target_zone(dma_target_zone),
        .irq_guardian(irq_guardian),
        .violation_count(violation_count)
    );

    always #5 clk = ~clk;

    task automatic pulse_access(
        input logic write_request,
        input logic [2:0] requester,
        input logic [31:0] address
    );
        begin
            @(negedge clk);
            access_write = write_request;
            requester_zone = requester;
            access_addr = address;
            access_valid = 1'b1;
            @(posedge clk);
            #1;
            access_valid = 1'b0;
        end
    endtask

    task automatic pulse_dma(
        input logic [6:0] domain_mask,
        input logic [31:0] source_addr,
        input logic [31:0] target_addr
    );
        begin
            @(negedge clk);
            dma_domain_mask = domain_mask;
            dma_source_addr = source_addr;
            dma_target_addr = target_addr;
            dma_valid = 1'b1;
            @(posedge clk);
            #1;
            dma_valid = 1'b0;
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

    initial begin
        repeat (2) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);
        #1;

        mmio_read(REG_STATUS, value);
        if (value[0] !== 1'b1) $fatal(1, "Guardian must be enforcing");
        if (value[1] !== 1'b1) $fatal(1, "Human Authority must remain final");
        if (value[2] !== 1'b0) $fatal(1, "Real DMA must remain disabled");
        if (value[3] !== 1'b0) $fatal(1, "External execution must remain disabled");

        // Public memory is shareable across zones.
        pulse_access(1'b0, Z_PRIVATE, 32'h2300_0010);
        if (access_allow !== 1'b1 || access_block !== 1'b0)
            $fatal(1, "Public read should be allowed");
        if (access_target_zone !== Z_PUBLIC)
            $fatal(1, "Public address decoded to wrong zone");

        // Private memory is isolated from Public Zone requesters.
        pulse_access(1'b0, Z_PUBLIC, 32'h2200_0020);
        if (access_allow !== 1'b0 || access_block !== 1'b1)
            $fatal(1, "Cross-zone private access must be blocked");
        if (access_target_zone !== Z_PRIVATE)
            $fatal(1, "Private address decoded to wrong zone");
        if (irq_guardian !== 1'b1)
            $fatal(1, "Protected-memory violation must raise Guardian IRQ");
        if (violation_count !== 32'd1)
            $fatal(1, "Violation count should be one");

        mmio_write_word(REG_IRQ_ACK, 32'h1);
        if (irq_guardian !== 1'b0)
            $fatal(1, "Guardian IRQ acknowledgement failed");

        // Same-zone Private access is allowed.
        pulse_access(1'b1, Z_PRIVATE, 32'h2200_0030);
        if (access_allow !== 1'b1 || access_block !== 1'b0)
            $fatal(1, "Private same-zone write should be allowed");

        // Recovery/boot ROM is never writable, even from Recovery Zone.
        pulse_access(1'b1, Z_RECOVERY, 32'h0000_0040);
        if (access_block !== 1'b1 || access_target_zone !== Z_RECOVERY)
            $fatal(1, "Recovery write must fail closed");
        if (violation_count !== 32'd2)
            $fatal(1, "Recovery write should increment violation count");

        mmio_write_word(REG_IRQ_ACK, 32'h1);

        // IOMMU-style domain permitting Public + Device classifies the DMA as
        // allowed, but this module has no DMA data path and performs no transfer.
        pulse_dma(7'b0100001, 32'h2300_0100, 32'h2400_0200);
        if (dma_allow !== 1'b1 || dma_block !== 1'b0)
            $fatal(1, "Public-to-Device DMA domain should classify as allowed");
        if (dma_source_zone !== Z_PUBLIC || dma_target_zone !== Z_DEVICE)
            $fatal(1, "DMA zones decoded incorrectly");

        // The same domain may not reach HRM.
        pulse_dma(7'b0100001, 32'h2300_0100, 32'h2000_0200);
        if (dma_allow !== 1'b0 || dma_block !== 1'b1)
            $fatal(1, "DMA domain expansion into HRM must be blocked");
        if (dma_target_zone !== Z_HRM)
            $fatal(1, "HRM DMA target decoded incorrectly");
        if (violation_count !== 32'd3)
            $fatal(1, "Blocked DMA should increment violation count");

        mmio_write_word(REG_IRQ_ACK, 32'h1);

        // Addresses outside the canonical map fail closed.
        pulse_access(1'b0, Z_DEVICE, 32'h3000_0000);
        if (access_block !== 1'b1)
            $fatal(1, "Unknown address must fail closed");
        if (violation_count !== 32'd4)
            $fatal(1, "Unknown address should increment violation count");

        // Protected status registers are read-only; attempted mutation itself is
        // a Guardian violation and cannot enable DMA or external execution.
        mmio_write_word(REG_STATUS, 32'hffff_ffff);
        if (irq_guardian !== 1'b1)
            $fatal(1, "Protected status write must raise Guardian IRQ");
        if (violation_count !== 32'd5)
            $fatal(1, "Protected MMIO write should increment violation count");

        mmio_read(REG_STATUS, value);
        if (value[2] !== 1'b0 || value[3] !== 1'b0)
            $fatal(1, "Protected write must not enable real DMA/execution");
        mmio_read(REG_IRQ_STATUS, value);
        if (value[0] !== 1'b1)
            $fatal(1, "Guardian IRQ status bit missing");
        mmio_read(REG_VIOLATIONS, value);
        if (value !== 32'd5)
            $fatal(1, "Final violation count mismatch");

        // Keep unused zone constants part of the elaborated proof contract.
        if (Z_SMI == Z_HRM || Z_GUARDIAN == Z_DEVICE)
            $fatal(1, "Zone encoding collision");

        $display("OAP_RTL_MEMORY_GUARD_V0_PASS");
        $finish;
    end

endmodule
