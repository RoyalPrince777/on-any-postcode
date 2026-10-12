package com.onanypostcode.oapworld;

import android.content.Context;

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
