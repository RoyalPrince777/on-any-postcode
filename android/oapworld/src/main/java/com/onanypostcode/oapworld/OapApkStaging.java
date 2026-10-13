package com.onanypostcode.oapworld;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;

/**
 * Copies a locally supplied APK into a private, bounded staging directory.
 * This does NOT authenticate the release or authorize installation.
 * Callers must re-verify the staged bytes and their signer before any use.
 */
public final class OapApkStaging {
    public static final long MAX_APK_BYTES = 256L * 1024 * 1024;
    private OapApkStaging() {}

    public static File stage(File source, File privateDirectory) throws IOException {
        return stage(source, privateDirectory, null);
    }

    /** Digest-checks temporary bytes before publishing them to the staging slot. */
    public static File stage(File source, File privateDirectory,
                             OapReleaseMetadata metadata) throws IOException {
        if (source == null || privateDirectory == null || !source.isFile()
                || !source.canRead() || source.length() <= 0
                || source.length() > MAX_APK_BYTES
                || !privateDirectory.isDirectory()) {
            throw new IOException("Invalid APK staging input");
        }
        if (Files.isSymbolicLink(privateDirectory.toPath())
                || Files.isSymbolicLink(source.toPath())) {
            throw new IOException("Symbolic links are not accepted");
        }
        File canonicalDirectory = privateDirectory.getCanonicalFile();
        File canonicalSource = source.getCanonicalFile();
        File destination = new File(canonicalDirectory, "oap-candidate.apk");
        if (Files.isSymbolicLink(destination.toPath())) {
            throw new IOException("Staging destination is a symbolic link");
        }
        if (canonicalSource.equals(destination.getCanonicalFile())) {
            throw new IOException("Source cannot be staging destination");
        }
        File temporary = File.createTempFile("oap-stage-", ".tmp", canonicalDirectory);
        boolean success = false;
        try {
            long copied = 0;
            try (FileInputStream input = new FileInputStream(canonicalSource);
                 FileOutputStream output = new FileOutputStream(temporary)) {
                byte[] buffer = new byte[64 * 1024];
                int count;
                while ((count = input.read(buffer)) != -1) {
                    copied += count;
                    if (copied > MAX_APK_BYTES) throw new IOException("APK exceeds size limit");
                    output.write(buffer, 0, count);
                }
                output.getFD().sync();
            }
            if (copied == 0 || copied != canonicalSource.length()) {
                throw new IOException("APK changed during staging");
            }
            if (metadata != null) {
                try (FileInputStream check = new FileInputStream(temporary)) {
                    if (!OapApkDigest.matches(check, metadata)) {
                        throw new IOException("Staged APK digest mismatch");
                    }
                }
            }
            // Atomic replacement avoids exposing a partially written APK.
            // Never delete a previously staged candidate before replacement.
            Files.move(temporary.toPath(), destination.toPath(),
                    StandardCopyOption.ATOMIC_MOVE,
                    StandardCopyOption.REPLACE_EXISTING);
            success = true;
            return destination;
        } finally {
            if (!success) temporary.delete();
        }
    }
}
