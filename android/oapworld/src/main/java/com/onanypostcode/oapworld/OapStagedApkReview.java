package com.onanypostcode.oapworld;

import android.content.Context;
import java.io.File;
import java.io.IOException;

/**
 * Founder-private, read-only staging plus verification entry point.
 * No network access, approval, PackageInstaller or installation side effects.
 * The staged file must be kept private and independently rechecked before use.
 */
public final class OapStagedApkReview {
    private OapStagedApkReview() {}

    public enum Result {
        INVALID_INPUT, STAGING_FAILED, LOCAL_VERIFICATION_FAILED,
        VERIFIED_LOCAL_ONLY
    }

    public static Result review(Context context, File source,
                                OapReleaseMetadata metadata, long installedVersionCode) {
        if (context == null || source == null || metadata == null
                || installedVersionCode < 0) return Result.INVALID_INPUT;
        File directory = new File(context.getFilesDir(), "oap-release-staging");
        if (!directory.isDirectory() && !directory.mkdir()) return Result.STAGING_FAILED;
        try {
            File staged = OapApkStaging.stage(source, directory);
            OapLocalApkVerifier.Result local =
                    OapLocalApkVerifier.verify(context, staged, metadata, installedVersionCode);
            return local == OapLocalApkVerifier.Result.VERIFIED_LOCAL_ONLY
                    ? Result.VERIFIED_LOCAL_ONLY : Result.LOCAL_VERIFICATION_FAILED;
        } catch (IOException | SecurityException e) {
            return Result.STAGING_FAILED;
        }
    }
}
