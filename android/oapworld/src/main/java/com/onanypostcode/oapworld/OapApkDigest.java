package com.onanypostcode.oapworld;

import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/**
 * Streaming SHA-256 for downloaded APK bytes.
 * This checks integrity against an expected digest only; a digest supplied by
 * an unauthenticated source does not authenticate a release or its signer.
 */
public final class OapApkDigest {
    private OapApkDigest() {}

    public static String sha256(InputStream stream) throws IOException {
        if (stream == null) throw new IllegalArgumentException("missing APK stream");
        final MessageDigest digest;
        try {
            digest = MessageDigest.getInstance("SHA-256");
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 unavailable", e);
        }
        byte[] buffer = new byte[8192];
        int read;
        while ((read = stream.read(buffer)) != -1) {
            if (read > 0) digest.update(buffer, 0, read);
        }
        byte[] hash = digest.digest();
        char[] out = new char[hash.length * 2];
        char[] hex = "0123456789abcdef".toCharArray();
        for (int i = 0; i < hash.length; i++) {
            out[2 * i] = hex[(hash[i] >>> 4) & 15];
            out[2 * i + 1] = hex[hash[i] & 15];
        }
        return new String(out);
    }

    public static boolean matches(InputStream apk, OapReleaseMetadata metadata)
            throws IOException {
        if (metadata == null) return false;
        return metadata.matchesSha256(sha256(apk));
    }
}
