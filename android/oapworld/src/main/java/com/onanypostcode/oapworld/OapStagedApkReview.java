package com.onanypostcode.oapworld;

import android.content.Context;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;

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
        // A private directory is required; reject symlink redirection.
        try {
            File appFiles = context.getFilesDir().getCanonicalFile();
            if (Files.isSymbolicLink(directory.toPath())
                    || !directory.getCanonicalFile().getParentFile().equals(appFiles)) {
                return Result.STAGING_FAILED;
            }
        } catch (IOException e) {
            return Result.STAGING_FAILED;
        }
        try {
            File staged = OapApkStaging.stage(source, directory);
            OapLocalApkVerifier.Result local =
                    OapLocalApkVerifier.verify(context, staged, metadata, installedVersionCode);
            if (local != OapLocalApkVerifier.Result.VERIFIED_LOCAL_ONLY) {
                // A failed review must not leave the candidate as a reusable artifact.
                staged.delete();
                return Result.LOCAL_VERIFICATION_FAILED;
            }
            return Result.VERIFIED_LOCAL_ONLY;
        } catch (IOException | SecurityException e) {
            return Result.STAGING_FAILED;
        }
    }
}
