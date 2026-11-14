package com.onanypostcode.oapworld;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.util.Arrays;

public final class OapApkStagingContractTest {
    private static void check(boolean value) {
        if (!value) throw new AssertionError("APK staging contract failed");
    }

    private static void write(File file, byte[] bytes) throws IOException {
        try (FileOutputStream out = new FileOutputStream(file)) {
            out.write(bytes);
        }
    }

    public static void main(String[] args) throws Exception {
        File root = Files.createTempDirectory("oap-staging-test").toFile();
        File privateDir = new File(root, "private");
        check(privateDir.mkdir());
        File source = new File(root, "source.apk");
        byte[] first = {1, 2, 3, 4};
        write(source, first);
        File staged = OapApkStaging.stage(source, privateDir);
        check(Arrays.equals(first, Files.readAllBytes(staged.toPath())));
        byte[] second = {5, 6};
        write(source, second);
        check(Arrays.equals(second, Files.readAllBytes(
                OapApkStaging.stage(source, privateDir).toPath())));
        check(Arrays.equals(second, Files.readAllBytes(source.toPath())));
        try {
            OapApkStaging.stage(staged, privateDir);
            throw new AssertionError("accepted self-overwrite");
        } catch (IOException expected) { }
        File empty = new File(root, "empty.apk");
        write(empty, new byte[0]);
        try {
            OapApkStaging.stage(empty, privateDir);
            throw new AssertionError("accepted empty APK");
        } catch (IOException expected) { }
        File symlink = new File(root, "linked.apk");
        Files.createSymbolicLink(symlink.toPath(), source.toPath());
        try {
            OapApkStaging.stage(symlink, privateDir);
            throw new AssertionError("accepted symlink");
        } catch (IOException expected) { }
        System.out.println("OAP APK staging contract: PASS");
    }
}
