package com.onanypostcode.oaphome;

import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Locale;

/**
 * Offline APK verification boundary. Never installs an APK or grants permissions.
 * Call only on a completed, private, non-world-writable local download.
 * This is not network transport verification or a replacement for Android's installer.
 */
public final class OapUpdateApkVerifier {
    private OapUpdateApkVerifier() {}

    public static final class VerifiedCandidate {
        public final File apk;
        public final String apkSha256;
        private VerifiedCandidate(File apk, String digest) {
            this.apk = apk;
            this.apkSha256 = digest;
        }
    }

    public static VerifiedCandidate verify(Context context, File apk,
            OapUpdateManifestPolicy.Candidate candidate) throws IOException {
        if (context == null || apk == null || candidate == null
                || !apk.isFile() || !apk.canRead() || apk.length() <= 0
                || apk.length() > 250L * 1024 * 1024) {
            throw new IOException("apk_missing_or_invalid");
        }
        // Limit input to the application private files directory; never trust a public path.
        File privateRoot = context.getFilesDir().getCanonicalFile();
        File canonicalApk = apk.getCanonicalFile();
        if (!canonicalApk.toPath().startsWith(privateRoot.toPath())
                || !canonicalApk.getName().endsWith(".apk")) {
            throw new IOException("apk_not_in_private_storage");
        }
        PackageManager manager = context.getPackageManager();
        try {
            PackageInfo installed = manager.getPackageInfo(candidate.packageName,
                    PackageManager.GET_SIGNATURES);
            PackageInfo archive = manager.getPackageArchiveInfo(canonicalApk.getAbsolutePath(),
                    PackageManager.GET_SIGNATURES);
            if (archive == null || !candidate.packageName.equals(archive.packageName)
                    || versionCode(archive) != candidate.versionCode
                    || versionCode(archive) <= versionCode(installed)) {
                throw new IOException("apk_package_or_version_mismatch");
            }
            String originalSigner = uniqueSignerSha256(installed.signatures);
            String candidateSigner = uniqueSignerSha256(archive.signatures);
            if (!originalSigner.equals(candidateSigner)
                    || !originalSigner.equals(candidate.signerSha256)) {
                throw new IOException("apk_signer_mismatch");
            }
            String actualDigest = fileSha256(canonicalApk);
            if (!actualDigest.equals(candidate.sha256)) {
                throw new IOException("apk_digest_mismatch");
            }
            return new VerifiedCandidate(canonicalApk, actualDigest);
        } catch (PackageManager.NameNotFoundException ex) {
            throw new IOException("installed_package_not_visible_or_missing", ex);
        }
    }

    private static long versionCode(PackageInfo info) {
        return android.os.Build.VERSION.SDK_INT >= 28
                ? info.getLongVersionCode() : info.versionCode;
    }

    private static String uniqueSignerSha256(Signature[] signatures) throws IOException {
        if (signatures == null || signatures.length != 1 || signatures[0] == null) {
            throw new IOException("apk_signer_not_unique");
        }
        try {
            return bytesToHex(MessageDigest.getInstance("SHA-256")
                    .digest(signatures[0].toByteArray()));
        } catch (NoSuchAlgorithmException ex) {
            throw new IOException("sha256_unavailable", ex);
        }
    }

    private static String fileSha256(File file) throws IOException {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[65536];
            try (FileInputStream stream = new FileInputStream(file)) {
                int n;
                while ((n = stream.read(buffer)) != -1) {
                    digest.update(buffer, 0, n);
                }
            }
            return bytesToHex(digest.digest());
        } catch (NoSuchAlgorithmException ex) {
            throw new IOException("sha256_unavailable", ex);
        }
    }

    private static String bytesToHex(byte[] value) {
        StringBuilder out = new StringBuilder(value.length * 2);
        for (byte b : value) out.append(String.format(Locale.ROOT, "%02x", b & 0xff));
        return out.toString();
    }
}
