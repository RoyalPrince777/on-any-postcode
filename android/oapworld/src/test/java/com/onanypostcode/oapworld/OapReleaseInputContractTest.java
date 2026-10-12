package com.onanypostcode.oapworld;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public final class OapReleaseInputContractTest {
    private static void check(boolean ok) {
        if (!ok) throw new AssertionError("release input contract failed");
    }
    private static void rejects(byte[] bytes) throws IOException {
        try {
            OapReleaseInput.read(new ByteArrayInputStream(bytes));
            throw new AssertionError("invalid input accepted");
        } catch (IllegalArgumentException expected) {
            // fail closed
        }
    }
    public static void main(String[] args) throws IOException {
        String valid = "package=com.onanypostcode.oapworld\nversionCode=2\nsha256="
                + "a".repeat(64);
        OapReleaseMetadata parsed = OapReleaseInput.read(
                new ByteArrayInputStream(valid.getBytes(StandardCharsets.US_ASCII)));
        check(parsed.versionCode == 2);
        rejects((valid + "x".repeat(600)).getBytes(StandardCharsets.US_ASCII));
        rejects(valid.replace("versionCode=2", "versionCode=0")
                .getBytes(StandardCharsets.US_ASCII));
        rejects((valid + "\r").getBytes(StandardCharsets.US_ASCII));
        rejects((valid + "\u0000").getBytes(StandardCharsets.US_ASCII));
        rejects((valid + "\u00e9").getBytes(StandardCharsets.UTF_8));
        try {
            OapReleaseInput.read(null);
            throw new AssertionError("null accepted");
        } catch (IllegalArgumentException expected) {
            // fail closed
        }
        System.out.println("OAP release input contract: PASS");
    }
}
