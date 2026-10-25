package com.onanypostcode.oapworld;

import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.os.Build;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/**
 * Local installed-package signer evidence. This does NOT inspect candidate
 * APK signatures or replace Android PackageManager's install-time checks.
 */
public final class OapInstalledSigner {
    private OapInstalledSigner() {}

    public static String sha256OfInstalledSigner(Context context) {
        if (context == null) return null;
        try {
            PackageManager manager = context.getPackageManager();
            PackageInfo info;
            Signature[] signatures;
            if (Build.VERSION.SDK_INT >= 28) {
                info = manager.getPackageInfo(context.getPackageName(),
                        PackageManager.GET_SIGNING_CERTIFICATES);
                if (info.signingInfo == null) return null;
                signatures = info.signingInfo.hasMultipleSigners()
                        ? info.signingInfo.getApkContentsSigners()
                        : info.signingInfo.getSigningCertificateHistory();
            } else {
                info = manager.getPackageInfo(context.getPackageName(),
                        PackageManager.GET_SIGNATURES);
                signatures = info.signatures;
            }
            // Fail closed for multiple certificates or signing rotation.
            // A full updater must evaluate Android's signing lineage rules.
            if (signatures == null || signatures.length != 1 || signatures[0] == null) {
                return null;
            }
            return sha256Hex(signatures[0].toByteArray());
        } catch (PackageManager.NameNotFoundException | SecurityException e) {
            return null;
        }
    }

    private static String sha256Hex(byte[] bytes) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(bytes);
            char[] result = new char[digest.length * 2];
            final String alphabet = "0123456789abcdef";
            for (int i = 0; i < digest.length; i++) {
                result[i * 2] = alphabet.charAt((digest[i] >>> 4) & 15);
                result[i * 2 + 1] = alphabet.charAt(digest[i] & 15);
            }
            return new String(result);
        } catch (NoSuchAlgorithmException e) {
            return null;
        }
    }
}
