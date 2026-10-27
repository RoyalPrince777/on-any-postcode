package com.onanypostcode.oaphome;

import org.json.JSONException;
import org.json.JSONObject;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.Locale;

/**
 * Source-only policy for future OAP Store updates.
 * Validating metadata does NOT authenticate the server, verify APK contents,
 * validate an installed certificate, download or install an update.
 */
public final class OapUpdateManifestPolicy {
    private static final String OWNED_HOST = "www.onanypostcode.com";
    private static final int MAX_MANIFEST_CHARS = 8192;

    private OapUpdateManifestPolicy() {}

    public static final class Candidate {
        public final String packageName;
        public final long versionCode;
        public final String apkUrl;
        public final String sha256;
        public final String signerSha256;

        private Candidate(String pkg, long code, String url, String hash, String signer) {
            packageName = pkg;
            versionCode = code;
            apkUrl = url;
            sha256 = hash;
            signerSha256 = signer;
        }
    }

    public static Candidate parse(String manifestJson, String installedPackage, long installedCode)
            throws JSONException {
        if (manifestJson == null || manifestJson.length() > MAX_MANIFEST_CHARS
                || installedPackage == null || installedCode < 0
                || !approvedPackage(installedPackage)) {
            throw new JSONException("update_manifest_rejected");
        }
        JSONObject obj = new JSONObject(manifestJson);
        if (obj.length() != 5) throw new JSONException("update_manifest_schema_rejected");
        String pkg = obj.getString("packageName");
        long version = obj.getLong("versionCode");
        String url = obj.getString("apkUrl");
        String hash = obj.getString("sha256");
        String signer = obj.getString("signerSha256");
        if (!installedPackage.equals(pkg) || version <= installedCode
                || !approvedPackage(pkg) || !hexDigest(hash) || !hexDigest(signer)
                || !approvedApkUrl(url)) {
            throw new JSONException("update_candidate_rejected");
        }
        return new Candidate(pkg, version, url, hash.toLowerCase(Locale.ROOT),
                signer.toLowerCase(Locale.ROOT));
    }

    private static boolean approvedPackage(String pkg) {
        return "com.onanypostcode.oaphome.v2".equals(pkg)
                || "com.onanypostcode.oapworld".equals(pkg);
    }

    private static boolean hexDigest(String value) {
        return value != null && value.matches("[A-Fa-f0-9]{64}");
    }

    private static boolean approvedApkUrl(String value) {
        try {
            URI uri = new URI(value);
            return "https".equals(uri.getScheme())
                    && OWNED_HOST.equals(uri.getHost())
                    && uri.getRawUserInfo() == null
                    && uri.getPort() == -1
                    && uri.getRawQuery() == null && uri.getRawFragment() == null
                    && uri.getRawPath() != null
                    && uri.getRawPath().startsWith("/oap-updates/apks/")
                    && uri.getRawPath().endsWith(".apk")
                    && !uri.getRawPath().contains("..")
                    && !uri.getRawPath().contains("%");
        } catch (URISyntaxException | IllegalArgumentException ex) {
            return false;
        }
    }
}
