package com.onanypostcode.oapworld;

import java.security.GeneralSecurityException;
import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.Signature;
import java.security.spec.X509EncodedKeySpec;
import android.util.Base64;

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
                || pinnedPublicKeyBase64 == null || pinnedPublicKeyBase64.isEmpty()) {
            return false;
        }
        try {
            byte[] keyBytes = Base64.decode(pinnedPublicKeyBase64, Base64.NO_WRAP);
            PublicKey key = KeyFactory.getInstance("Ed25519")
                    .generatePublic(new X509EncodedKeySpec(keyBytes));
            Signature verifier = Signature.getInstance("Ed25519");
            verifier.initVerify(key);
            verifier.update(canonicalReleaseBytes);
            return verifier.verify(detachedSignature);
        } catch (GeneralSecurityException | IllegalArgumentException e) {
            return false;
        }
    }
}
