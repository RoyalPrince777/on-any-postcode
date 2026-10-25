package com.onanypostcode.oapworld;

/** Dependency-free contract checks for the Founder update eligibility gate. */
public final class OapUpdateEligibilityContractTest {
    private static final String PKG = "com.onanypostcode.oapworld";
    private static void expect(OapUpdateEligibility.Decision expected,
                               String pkg, long code, boolean source,
                               boolean integrity, boolean signature, boolean governance) {
        OapUpdateEligibility.Decision actual = OapUpdateEligibility.evaluate(
                PKG, 1, pkg, code, source, integrity, signature, governance);
        if (actual != expected) {
            throw new AssertionError("expected " + expected + " but got " + actual);
        }
    }

    public static void main(String[] args) {
        expect(OapUpdateEligibility.Decision.BLOCK_WRONG_PACKAGE,
                "other.app", 2, true, true, true, true);
        expect(OapUpdateEligibility.Decision.BLOCK_NOT_NEWER,
                PKG, 1, true, true, true, true);
        expect(OapUpdateEligibility.Decision.BLOCK_NOT_NEWER,
                PKG, 0, true, true, true, true);
        expect(OapUpdateEligibility.Decision.BLOCK_UNVERIFIED_SOURCE,
                PKG, 2, false, true, true, true);
        expect(OapUpdateEligibility.Decision.BLOCK_UNVERIFIED_ARTIFACT,
                PKG, 2, true, false, true, true);
        expect(OapUpdateEligibility.Decision.BLOCK_UNVERIFIED_ARTIFACT,
                PKG, 2, true, true, false, true);
        expect(OapUpdateEligibility.Decision.BLOCK_GOVERNANCE,
                PKG, 2, true, true, true, false);
        expect(OapUpdateEligibility.Decision.ELIGIBLE_FOR_FURTHER_VERIFICATION,
                PKG, 2, true, true, true, true);
        expect(OapUpdateEligibility.Decision.BLOCK_INVALID_METADATA,
                "", 2, true, true, true, true);
        expect(OapUpdateEligibility.Decision.BLOCK_INVALID_METADATA,
                PKG, -1, true, true, true, true);
        System.out.println("OAP update eligibility policy contract: PASS");
    }
}
