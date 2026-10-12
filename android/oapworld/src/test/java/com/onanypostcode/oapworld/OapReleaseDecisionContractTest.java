package com.onanypostcode.oapworld;

public final class OapReleaseDecisionContractTest {
    private static void check(boolean condition) {
        if (!condition) throw new AssertionError("release decision gate failed");
    }

    public static void main(String[] args) {
        for (OapLocalApkVerifier.Result local : OapLocalApkVerifier.Result.values()) {
            for (int bits = 0; bits < 8; bits++) {
                boolean authority = (bits & 1) != 0;
                boolean governance = (bits & 2) != 0;
                boolean consent = (bits & 4) != 0;
                OapReleaseDecision.Result actual = OapReleaseDecision.evaluate(
                        local, authority, governance, consent);
                boolean allPassed = local == OapLocalApkVerifier.Result.VERIFIED_LOCAL_ONLY
                        && authority && governance && consent;
                check((actual == OapReleaseDecision.Result.READY_FOR_PLATFORM_INSTALLER)
                        == allPassed);
            }
        }
        check(OapReleaseDecision.evaluate(null, true, true, true)
                == OapReleaseDecision.Result.BLOCK_LOCAL_VERIFICATION);
        System.out.println("OAP release decision contract: PASS");
    }
}
