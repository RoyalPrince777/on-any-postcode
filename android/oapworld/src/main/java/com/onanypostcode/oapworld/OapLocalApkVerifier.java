package com.onanypostcode.oapworld;

import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.os.Build;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;

/**
 * Read-only local candidate APK verification.
 *
 * A true result means ONLY that the candidate matches locally supplied
 * metadata and installed signing identity. It does not authenticate the
 * metadata's publisher, CI evidence, or authorise installation.
 */
public final class OapLocalApkVerifier {
    private OapLocalApkVerifier() {}

    public enum Result {
        INVALID_INPUT,
        MISSING_APK,
        WRONG_PACKAGE,
        NOT_NEWER,
        CANDIDATE_METADATA_MISMATCH,
        DIGEST_MISMATCH,
        SIGNER_MISMATCH,
        VERIFIED_LOCAL_ONLY
    }

    public static Result verify(Context context,
                                File apk,
                                OapReleaseMetadata metadata,
                                long installedVersionCode) {
        if (context == null || metadata == null || installedVersionCode < 0) {
            return Result.INVALID_INPUT;
        }
        if (apk == null || !apk.isFile() || !apk.canRead() || apk.length() <= 0) {
            return Result.MISSING_APK;
        }
        if (!context.getPackageName().equals(metadata.packageId)) {
            return Result.WRONG_PACKAGE;
        }
        if (metadata.versionCode <= installedVersionCode) {
            return Result.NOT_NEWER;
        }
        // Do not trust the text manifest's version/package assertions alone.
        // Compare them to the APK archive itself before accepting its digest.
        try {
            PackageInfo archive = context.getPackageManager().getPackageArchiveInfo(
                    apk.getAbsolutePath(), 0);
            if (archive == null || !context.getPackageName().equals(archive.packageName)) {
                return Result.CANDIDATE_METADATA_MISMATCH;
            }
            long archiveVersion = Build.VERSION.SDK_INT >= 28
                    ? archive.getLongVersionCode() : archive.versionCode;
            if (archiveVersion != metadata.versionCode || archiveVersion <= installedVersionCode) {
                return Result.CANDIDATE_METADATA_MISMATCH;
            }
        } catch (RuntimeException e) {
            return Result.CANDIDATE_METADATA_MISMATCH;
        }
        try (FileInputStream input = new FileInputStream(apk)) {
            if (!OapApkDigest.matches(input, metadata)) {
                return Result.DIGEST_MISMATCH;
            }
        } catch (IOException | SecurityException e) {
            return Result.DIGEST_MISMATCH;
        }
        if (!OapCandidateSigner.matchesInstalledSigner(context, apk)) {
            return Result.SIGNER_MISMATCH;
        }
        return Result.VERIFIED_LOCAL_ONLY;
    }
}
