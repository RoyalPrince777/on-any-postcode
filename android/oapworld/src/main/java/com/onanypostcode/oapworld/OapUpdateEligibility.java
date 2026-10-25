package com.onanypostcode.oapworld;

/**
 * Pure-Java fail-closed release eligibility gate.
 * This is a policy helper, NOT release authentication, APK signature
 * verification, an updater, or permission to install anything.
 */
public final class OapUpdateEligibility {
    private OapUpdateEligibility() {}

    public enum Decision {
        ELIGIBLE_FOR_FURTHER_VERIFICATION,
        BLOCK_INVALID_METADATA,
        BLOCK_WRONG_PACKAGE,
        BLOCK_NOT_NEWER,
        BLOCK_UNVERIFIED_SOURCE,
        BLOCK_UNVERIFIED_ARTIFACT,
        BLOCK_GOVERNANCE
    }

    public static Decision evaluate(String installedPackage,
                                    long installedVersion,
                                    String candidatePackage,
                                    long candidateVersion,
                                    boolean trustedReleaseSource,
                                    boolean artifactIntegrityVerified,
                                    boolean signingContinuityVerified,
                                    boolean governedChecksPassed) {
        if (installedPackage == null || installedPackage.isEmpty()
                || candidatePackage == null || candidatePackage.isEmpty()
                || installedVersion < 0 || candidateVersion < 0) {
            return Decision.BLOCK_INVALID_METADATA;
        }
        if (!installedPackage.equals(candidatePackage)) {
            return Decision.BLOCK_WRONG_PACKAGE;
        }
        if (candidateVersion <= installedVersion) {
            return Decision.BLOCK_NOT_NEWER;
        }
        if (!trustedReleaseSource) {
            return Decision.BLOCK_UNVERIFIED_SOURCE;
        }
        if (!artifactIntegrityVerified || !signingContinuityVerified) {
            return Decision.BLOCK_UNVERIFIED_ARTIFACT;
        }
        if (!governedChecksPassed) {
            return Decision.BLOCK_GOVERNANCE;
        }
        return Decision.ELIGIBLE_FOR_FURTHER_VERIFICATION;
    }
}
