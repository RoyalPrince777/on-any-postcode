package com.onanypostcode.oapworld;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.security.GeneralSecurityException;
import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.Signature;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

/**
 * Independent Ed25519 signature verification of canonical release bytes.
 * The public key MUST come from an independently trusted, pinned OAP key.
 * Never fetch the verification key alongside untrusted release data.
 */
public final class OapReleaseAuthority {
    private OapReleaseAuthority() {}

    public static boolean verify(byte[] canonicalReleaseBytes,
                                 byte[] detachedSignature,
                                 String pinnedPublicKeyBase64) {
        if (canonicalReleaseBytes == null || canonicalReleaseBytes.length == 0
                || canonicalReleaseBytes.length > 512
                || detachedSignature == null || detachedSignature.length != 64
                || pinnedPublicKeyBase64 == null || pinnedPublicKeyBase64.length() > 256
                || pinnedPublicKeyBase64.isEmpty()) {
            return false;
        }
        try {
            // A valid signature over arbitrary bytes is not a valid OAP release.
            // Apply the same bounded canonical parser used by release ingestion.
            OapReleaseMetadata release = OapReleaseInput.read(new ByteArrayInputStream(canonicalReleaseBytes));
            if (!"com.onanypostcode.oapworld".equals(release.packageId)) return false;
            byte[] keyBytes = Base64.getDecoder().decode(pinnedPublicKeyBase64);
            PublicKey key = KeyFactory.getInstance("Ed25519")
                    .generatePublic(new X509EncodedKeySpec(keyBytes));
            Signature verifier = Signature.getInstance("Ed25519");
            verifier.initVerify(key);
            verifier.update(canonicalReleaseBytes);
            return verifier.verify(detachedSignature);
        } catch (GeneralSecurityException | IllegalArgumentException | IOException e) {
            return false;
        }
    }
}
