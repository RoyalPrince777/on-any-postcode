package com.onanypostcode.oapworld;

public final class OapReleaseMetadataContractTest {
    private static void rejected(String metadata) {
        try {
            OapReleaseMetadata.parse(metadata);
            throw new AssertionError("accepted invalid release metadata");
        } catch (IllegalArgumentException expected) {
            // Fail closed.
        }
    }
    public static void main(String[] args) {
        String hash = "a".repeat(64);
        String valid = "package=com.onanypostcode.oapworld\nversionCode=2\nsha256=" + hash;
        OapReleaseMetadata parsed = OapReleaseMetadata.parse(valid);
        if (!parsed.packageId.equals("com.onanypostcode.oapworld") ||
                parsed.versionCode != 2 || !parsed.matchesSha256(hash)) {
            throw new AssertionError("valid metadata parse failed");
        }
        rejected(null);
        rejected("");
        rejected(valid + "\n");
        rejected(valid + "\nversionCode=3");
        rejected(valid.replace("versionCode=2", "versionCode=0"));
        rejected(valid.replace("versionCode=2", "versionCode=-1"));
        rejected(valid.replace("versionCode=2", "versionCode=02"));
        rejected(valid.replace(hash, "Z".repeat(64)));
        rejected(valid.replace(hash, "a".repeat(63)));
        rejected(valid.replace("package=", "other="));
        rejected(valid.replace("\n", "\r\n"));
        System.out.println("OAP release metadata contract: PASS");
    }
}
