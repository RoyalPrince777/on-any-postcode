package com.onanypostcode.oapworld;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public final class OapApkDigestContractTest {
    private static void assertTrue(boolean value) {
        if (!value) throw new AssertionError("digest contract failed");
    }

    public static void main(String[] args) throws IOException {
        byte[] payload = "abc".getBytes(StandardCharsets.UTF_8);
        String expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
        String actual = OapApkDigest.sha256(new ByteArrayInputStream(payload));
        assertTrue(expected.equals(actual));
        String metadata = "package=com.onanypostcode.oapworld\nversionCode=2\nsha256=" + expected;
        OapReleaseMetadata parsed = OapReleaseMetadata.parse(metadata);
        assertTrue(OapApkDigest.matches(new ByteArrayInputStream(payload), parsed));
        assertTrue(!OapApkDigest.matches(new ByteArrayInputStream(
                "tampered".getBytes(StandardCharsets.UTF_8)), parsed));
        assertTrue(!OapApkDigest.matches(new ByteArrayInputStream(payload), null));
        try {
            OapApkDigest.sha256(null);
            throw new AssertionError("null stream accepted");
        } catch (IllegalArgumentException expectedFailure) {
            // expected
        }
        System.out.println("OAP APK SHA-256 contract: PASS");
    }
}
