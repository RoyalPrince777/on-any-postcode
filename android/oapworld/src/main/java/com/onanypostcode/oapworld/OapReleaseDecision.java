package com.onanypostcode.oapworld;

/**
 * Founder release decision gate. Local APK checks alone cannot authorize an
 * installation. Callers must supply independently verified evidence.
 *
 * No installation or download is performed here.
 */
public final class OapReleaseDecision {
    private OapReleaseDecision() {}

    public enum Result {
        BLOCK_LOCAL_VERIFICATION,
        BLOCK_RELEASE_AUTHORITY,
        BLOCK_GOVERNANCE,
        BLOCK_FOUNDER_CONSENT,
        READY_FOR_PLATFORM_INSTALLER
    }

    public static Result evaluate(
            OapLocalApkVerifier.Result localResult,
            boolean releaseAuthorityVerified,
            boolean exactArtifactGovernanceVerified,
            boolean founderApprovedThisArtifact) {
        if (localResult != OapLocalApkVerifier.Result.VERIFIED_LOCAL_ONLY) {
            return Result.BLOCK_LOCAL_VERIFICATION;
        }
        if (!releaseAuthorityVerified) return Result.BLOCK_RELEASE_AUTHORITY;
        if (!exactArtifactGovernanceVerified) return Result.BLOCK_GOVERNANCE;
        if (!founderApprovedThisArtifact) return Result.BLOCK_FOUNDER_CONSENT;
        return Result.READY_FOR_PLATFORM_INSTALLER;
    }
}
