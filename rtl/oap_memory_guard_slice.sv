`timescale 1ns/1ps

// OAP RTL Memory Guard / IOMMU Proof Slice v0
//
// Hardware-description proof of address-zone isolation and DMA-domain policy.
// This slice classifies requests and emits allow/block results only. It contains
// no memory data path, no physical DMA engine and no external execution output.
// SMI remains the single Brain and Human Authority remains final above hardware.

module oap_memory_guard_slice (
    input  logic        clk,
    input  logic        rst_n,

    input  logic        access_valid,
    input  logic        access_write,
    input  logic [2:0]  requester_zone,
    input  logic [31:0] access_addr,

    input  logic        dma_valid,
    input  logic [6:0]  dma_domain_mask,
    input  logic [31:0] dma_source_addr,
    input  logic [31:0] dma_target_addr,

    input  logic        mmio_valid,
    input  logic        mmio_write,
    input  logic [7:0]  mmio_addr,
    input  logic [31:0] mmio_wdata,
    output logic [31:0] mmio_rdata,
    output logic        mmio_ready,

    output logic        access_allow,
    output logic        access_block,
    output logic [2:0]  access_target_zone,
    output logic        dma_allow,
    output logic        dma_block,
    output logic [2:0]  dma_source_zone,
    output logic [2:0]  dma_target_zone,
    output logic        irq_guardian,
    output logic [31:0] violation_count
);

    localparam logic [2:0] Z_PUBLIC   = 3'd0;
    localparam logic [2:0] Z_PRIVATE  = 3'd1;
    localparam logic [2:0] Z_SMI      = 3'd2;
    localparam logic [2:0] Z_HRM      = 3'd3;
    localparam logic [2:0] Z_GUARDIAN = 3'd4;
    localparam logic [2:0] Z_DEVICE   = 3'd5;
    localparam logic [2:0] Z_RECOVERY = 3'd6;

    localparam logic [7:0] REG_STATUS       = 8'h00;
    localparam logic [7:0] REG_VIOLATIONS   = 8'h04;
    localparam logic [7:0] REG_LAST_ACCESS  = 8'h08;
    localparam logic [7:0] REG_LAST_DMA     = 8'h0c;
    localparam logic [7:0] REG_IRQ_STATUS   = 8'h10;
    localparam logic [7:0] REG_IRQ_ACK      = 8'h14;

    logic last_access_allowed;
    logic last_access_blocked;
    logic last_access_write;
    logic last_dma_allowed;
    logic last_dma_blocked;

    logic access_addr_valid;
    logic dma_source_valid;
    logic dma_target_valid;
    logic [2:0] decoded_access_zone;
    logic [2:0] decoded_dma_source_zone;
    logic [2:0] decoded_dma_target_zone;
    logic access_policy_allow;
    logic access_policy_block;
    logic dma_policy_allow;
    logic dma_policy_block;
    logic protected_mmio_write;
    logic [2:0] violation_events;

    function automatic logic address_valid(input logic [31:0] addr);
        begin
            address_valid =
                ((addr >= 32'h0000_0000) && (addr <= 32'h0000_ffff)) ||
                ((addr >= 32'h1000_0000) && (addr <= 32'h1000_3fff)) ||
                ((addr >= 32'h2000_0000) && (addr <= 32'h200f_ffff)) ||
                ((addr >= 32'h2100_0000) && (addr <= 32'h210f_ffff)) ||
                ((addr >= 32'h2200_0000) && (addr <= 32'h220f_ffff)) ||
                ((addr >= 32'h2300_0000) && (addr <= 32'h230f_ffff)) ||
                ((addr >= 32'h2400_0000) && (addr <= 32'h240f_ffff));
        end
    endfunction

    function automatic logic [2:0] zone_for(input logic [31:0] addr);
        begin
            if ((addr >= 32'h0000_0000) && (addr <= 32'h0000_ffff))
                zone_for = Z_RECOVERY;
            else if (((addr >= 32'h1000_0000) && (addr <= 32'h1000_0fff)) ||
                     ((addr >= 32'h1000_3000) && (addr <= 32'h1000_3fff)))
                zone_for = Z_GUARDIAN;
            else if ((addr >= 32'h1000_1000) && (addr <= 32'h1000_2fff))
                zone_for = Z_DEVICE;
            else if ((addr >= 32'h2000_0000) && (addr <= 32'h200f_ffff))
                zone_for = Z_HRM;
            else if ((addr >= 32'h2100_0000) && (addr <= 32'h210f_ffff))
                zone_for = Z_SMI;
            else if ((addr >= 32'h2200_0000) && (addr <= 32'h220f_ffff))
                zone_for = Z_PRIVATE;
            else if ((addr >= 32'h2300_0000) && (addr <= 32'h230f_ffff))
                zone_for = Z_PUBLIC;
            else
                zone_for = Z_DEVICE;
        end
    endfunction

    function automatic logic zone_is_protected(input logic [2:0] zone);
        begin
            zone_is_protected =
                (zone == Z_PRIVATE) ||
                (zone == Z_SMI) ||
                (zone == Z_HRM) ||
                (zone == Z_GUARDIAN) ||
                (zone == Z_RECOVERY);
        end
    endfunction

    always @* begin
        access_addr_valid = address_valid(access_addr);
        decoded_access_zone = zone_for(access_addr);
        access_policy_allow = 1'b0;
        access_policy_block = 1'b0;

        if (access_valid) begin
            if (!access_addr_valid)
                access_policy_block = 1'b1;
            else if (access_write && decoded_access_zone == Z_RECOVERY)
                access_policy_block = 1'b1;
            else if (zone_is_protected(decoded_access_zone) && requester_zone != decoded_access_zone)
                access_policy_block = 1'b1;
            else
                access_policy_allow = 1'b1;
        end
    end

    always @* begin
        dma_source_valid = address_valid(dma_source_addr);
        dma_target_valid = address_valid(dma_target_addr);
        decoded_dma_source_zone = zone_for(dma_source_addr);
        decoded_dma_target_zone = zone_for(dma_target_addr);
        dma_policy_allow = 1'b0;
        dma_policy_block = 1'b0;

        if (dma_valid) begin
            if (!dma_source_valid || !dma_target_valid)
                dma_policy_block = 1'b1;
            else if (decoded_dma_source_zone == Z_RECOVERY || decoded_dma_target_zone == Z_RECOVERY)
                dma_policy_block = 1'b1;
            else if (!dma_domain_mask[decoded_dma_source_zone] || !dma_domain_mask[decoded_dma_target_zone])
                dma_policy_block = 1'b1;
            else
                dma_policy_allow = 1'b1;
        end
    end

    always @* begin
        protected_mmio_write = mmio_valid && mmio_write &&
            (mmio_addr == REG_STATUS ||
             mmio_addr == REG_VIOLATIONS ||
             mmio_addr == REG_LAST_ACCESS ||
             mmio_addr == REG_LAST_DMA ||
             mmio_addr == REG_IRQ_STATUS);

        violation_events = 3'd0;
        if (access_valid && access_policy_block)
            violation_events = violation_events + 1'b1;
        if (dma_valid && dma_policy_block)
            violation_events = violation_events + 1'b1;
        if (protected_mmio_write)
            violation_events = violation_events + 1'b1;
    end

    assign mmio_ready = mmio_valid;

    always @* begin
        mmio_rdata = 32'h0000_0000;
        case (mmio_addr)
            REG_STATUS: begin
                // bit 0: Guardian enforcing (1)
                // bit 1: Human Authority final (1)
                // bit 2: real DMA enabled (0)
                // bit 3: external execution enabled (0)
                // bit 4: Guardian violation interrupt pending
                mmio_rdata = {27'h0, irq_guardian, 2'b00, 2'b11};
            end
            REG_VIOLATIONS: mmio_rdata = violation_count;
            REG_LAST_ACCESS: mmio_rdata = {
                21'h0,
                last_access_write,
                last_access_blocked,
                last_access_allowed,
                5'h0,
                access_target_zone
            };
            REG_LAST_DMA: mmio_rdata = {
                22'h0,
                last_dma_blocked,
                last_dma_allowed,
                1'b0,
                dma_target_zone,
                1'b0,
                dma_source_zone
            };
            REG_IRQ_STATUS: mmio_rdata = {31'h0, irq_guardian};
            default: mmio_rdata = 32'h0000_0000;
        endcase
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            access_allow       <= 1'b0;
            access_block       <= 1'b0;
            access_target_zone <= Z_DEVICE;
            dma_allow          <= 1'b0;
            dma_block          <= 1'b0;
            dma_source_zone    <= Z_DEVICE;
            dma_target_zone    <= Z_DEVICE;
            irq_guardian       <= 1'b0;
            violation_count    <= 32'h0000_0000;
            last_access_allowed <= 1'b0;
            last_access_blocked <= 1'b0;
            last_access_write   <= 1'b0;
            last_dma_allowed    <= 1'b0;
            last_dma_blocked    <= 1'b0;
        end else begin
            access_allow <= 1'b0;
            access_block <= 1'b0;
            dma_allow    <= 1'b0;
            dma_block    <= 1'b0;

            if (mmio_valid && mmio_write && mmio_addr == REG_IRQ_ACK && mmio_wdata[0])
                irq_guardian <= 1'b0;

            if (access_valid) begin
                access_target_zone <= decoded_access_zone;
                access_allow <= access_policy_allow;
                access_block <= access_policy_block;
                last_access_allowed <= access_policy_allow;
                last_access_blocked <= access_policy_block;
                last_access_write <= access_write;
            end

            if (dma_valid) begin
                dma_source_zone <= decoded_dma_source_zone;
                dma_target_zone <= decoded_dma_target_zone;
                dma_allow <= dma_policy_allow;
                dma_block <= dma_policy_block;
                last_dma_allowed <= dma_policy_allow;
                last_dma_blocked <= dma_policy_block;
            end

            if (violation_events != 0) begin
                violation_count <= violation_count + violation_events;
                irq_guardian <= 1'b1;
            end
        end
    end

endmodule
