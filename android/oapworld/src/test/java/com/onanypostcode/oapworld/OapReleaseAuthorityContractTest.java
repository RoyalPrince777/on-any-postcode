package com.onanypostcode.oapworld;

import java.nio.charset.StandardCharsets;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.Signature;
import java.util.Base64;

public final class OapReleaseAuthorityContractTest {
    private static void check(boolean ok) {
        if (!ok) throw new AssertionError("OAP release authority contract failed");
    }

    public static void main(String[] args) throws Exception {
        KeyPairGenerator generator = KeyPairGenerator.getInstance("Ed25519");
        KeyPair trusted = generator.generateKeyPair();
        KeyPair impostor = generator.generateKeyPair();
        String pinned = Base64.getEncoder().encodeToString(trusted.getPublic().getEncoded());
        byte[] release = ("package=com.onanypostcode.oapworld\nversionCode=2\nsha256="
                + "a".repeat(64)).getBytes(StandardCharsets.US_ASCII);
        Signature signer = Signature.getInstance("Ed25519");
        signer.initSign(trusted.getPrivate());
        signer.update(release);
        byte[] signature = signer.sign();
        check(OapReleaseAuthority.verify(release, signature, pinned));
        byte[] tampered = release.clone();
        tampered[20] ^= 1;
        check(!OapReleaseAuthority.verify(tampered, signature, pinned));
        check(!OapReleaseAuthority.verify(release, signature,
                Base64.getEncoder().encodeToString(impostor.getPublic().getEncoded())));
        byte[] badSignature = signature.clone();
        badSignature[0] ^= 1;
        check(!OapReleaseAuthority.verify(release, badSignature, pinned));
        check(!OapReleaseAuthority.verify(null, signature, pinned));
        check(!OapReleaseAuthority.verify(release, null, pinned));
        check(!OapReleaseAuthority.verify(release, signature, "invalid key!"));
        check(!OapReleaseAuthority.verify(new byte[513], signature, pinned));
        // Even a legitimately signed payload is rejected unless its content
        // conforms to the canonical OAP release schema.
        byte[] malformed = "package=other\\nversionCode=2\\nsha256=oops"
                .getBytes(StandardCharsets.US_ASCII);
        signer.initSign(trusted.getPrivate());
        signer.update(malformed);
        check(!OapReleaseAuthority.verify(malformed, signer.sign(), pinned));
        byte[] nonAscii = release.clone();
        nonAscii[0] = (byte) 0xff;
        signer.initSign(trusted.getPrivate());
        signer.update(nonAscii);
        check(!OapReleaseAuthority.verify(nonAscii, signer.sign(), pinned));
        check(!OapReleaseAuthority.verify(release, signature, "A".repeat(257)));
        byte[] wrongPackage = ("package=com.otherworld.app\\nversionCode=2\\nsha256="
                + "a".repeat(64)).getBytes(StandardCharsets.US_ASCII);
        signer.initSign(trusted.getPrivate());
        signer.update(wrongPackage);
        check(!OapReleaseAuthority.verify(wrongPackage, signer.sign(), pinned));
        System.out.println("OAP release authority contract: PASS");
    }
}
