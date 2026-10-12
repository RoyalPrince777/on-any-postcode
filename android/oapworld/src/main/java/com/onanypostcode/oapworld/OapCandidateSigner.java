package com.onanypostcode.oapworld;

import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.os.Build;

import java.io.File;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/**
 * Read-only signer compatibility check for a locally staged APK.
 * This does not download, install, or independently establish release provenance.
 * Android's PackageInstaller remains the authority at installation time.
 */
public final class OapCandidateSigner {
    private OapCandidateSigner() {}

    public static boolean matchesInstalledSigner(Context context, File candidateApk) {
        if (context == null || candidateApk == null || !candidateApk.isFile()
                || !candidateApk.canRead() || candidateApk.length() == 0) {
            return false;
        }
        String installed = OapInstalledSigner.sha256OfInstalledSigner(context);
        if (installed == null) return false;
        try {
            PackageManager pm = context.getPackageManager();
            PackageInfo candidate = pm.getPackageArchiveInfo(candidateApk.getAbsolutePath(),
                    Build.VERSION.SDK_INT >= 28
                            ? PackageManager.GET_SIGNING_CERTIFICATES
                            : PackageManager.GET_SIGNATURES);
            if (candidate == null || !context.getPackageName().equals(candidate.packageName)) {
                return false;
            }
            Signature[] signers;
            if (Build.VERSION.SDK_INT >= 28) {
                if (candidate.signingInfo == null) return false;
                // Explicitly block multiple signers and rotation until lineage-aware
                // verification is implemented and tested.
                if (candidate.signingInfo.hasMultipleSigners()) return false;
                signers = candidate.signingInfo.getSigningCertificateHistory();
            } else {
                signers = candidate.signatures;
            }
            if (signers == null || signers.length != 1 || signers[0] == null) return false;
            return installed.equals(fingerprint(signers[0].toByteArray()));
        } catch (RuntimeException e) {
            return false;
        }
    }

    private static String fingerprint(byte[] bytes) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(bytes);
            StringBuilder result = new StringBuilder(64);
            for (byte b : digest) {
                result.append(Character.forDigit((b >>> 4) & 15, 16));
                result.append(Character.forDigit(b & 15, 16));
            }
            return result.toString();
        } catch (NoSuchAlgorithmException e) {
            return null;
        }
    }
}
