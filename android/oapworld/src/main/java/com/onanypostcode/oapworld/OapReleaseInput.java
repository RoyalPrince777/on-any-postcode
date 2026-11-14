package com.onanypostcode.oapworld;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/**
 * Bounded, fail-closed parsing of first-party release information.
 * This is only an input boundary; it does NOT authenticate the source.
 */
public final class OapReleaseInput {
    private static final int MAX_BYTES = 512;
    private OapReleaseInput() {}

    public static OapReleaseMetadata read(InputStream input) throws IOException {
        if (input == null) throw new IllegalArgumentException("missing release input");
        byte[] bytes = new byte[MAX_BYTES + 1];
        int used = 0;
        while (used < bytes.length) {
            int n = input.read(bytes, used, bytes.length - used);
            if (n == -1) break;
            if (n == 0) {
                int one = input.read();
                if (one == -1) break;
                bytes[used++] = (byte) one;
            } else {
                used += n;
            }
        }
        if (used > MAX_BYTES) throw new IllegalArgumentException("release input too large");
        for (int i = 0; i < used; i++) {
            if ((bytes[i] & 0x80) != 0 || bytes[i] == 0) {
                throw new IllegalArgumentException("non-canonical release input");
            }
        }
        return OapReleaseMetadata.parse(new String(bytes, 0, used, StandardCharsets.US_ASCII));
    }
}
