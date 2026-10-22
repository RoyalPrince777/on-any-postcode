package com.onanypostcode.oapworld;

import java.util.Locale;

/**
 * Pure-Java metadata parser. Metadata is UNTRUSTED until its source,
 * artifact digest, APK signer and governance evidence are independently verified.
 */
public final class OapReleaseMetadata {
    public final String packageId;
    public final long versionCode;
    public final String sha256;

    private OapReleaseMetadata(String packageId, long versionCode, String sha256) {
        this.packageId = packageId;
        this.versionCode = versionCode;
        this.sha256 = sha256;
    }

    /**
     * Strict three-line canonical format, no duplicates or additional fields:
     * package=com.onanypostcode.oapworld
     * versionCode=2
     * sha256=<64 lowercase hexadecimal characters>
     */
    public static OapReleaseMetadata parse(String text) {
        if (text == null || text.length() > 512 || text.indexOf('\r') >= 0) {
            throw new IllegalArgumentException("invalid metadata");
        }
        String[] lines = text.split("\n", -1);
        if (lines.length != 3) throw new IllegalArgumentException("invalid line count");
        String packagePrefix = "package=";
        String versionPrefix = "versionCode=";
        String hashPrefix = "sha256=";
        if (!lines[0].startsWith(packagePrefix) ||
                !lines[1].startsWith(versionPrefix) ||
                !lines[2].startsWith(hashPrefix)) {
            throw new IllegalArgumentException("invalid fields");
        }
        String pkg = lines[0].substring(packagePrefix.length());
        String code = lines[1].substring(versionPrefix.length());
        String hash = lines[2].substring(hashPrefix.length());
        if (!pkg.matches("[a-zA-Z][a-zA-Z0-9_]*(\\.[a-zA-Z][a-zA-Z0-9_]*)+")
                || !code.matches("[1-9][0-9]{0,17}")
                || !hash.matches("[0-9a-f]{64}")) {
            throw new IllegalArgumentException("invalid values");
        }
        try {
            return new OapReleaseMetadata(pkg, Long.parseLong(code), hash);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("invalid version", e);
        }
    }

    public boolean matchesSha256(String actualHash) {
        return actualHash != null &&
                sha256.equals(actualHash.toLowerCase(Locale.ROOT));
    }
}
