package com.onanypostcode.oapworld;

import android.net.Uri;
import android.os.Handler;
import android.os.Looper;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

public final class EngineDocumentClient {
    public interface Callback {
        void onEngineDocument(String json, String sourcePath);
        void onFallback(String sourcePath);
    }

    private static final int CONNECT_TIMEOUT_MS = 4000;
    private static final int READ_TIMEOUT_MS = 6000;
    private static final int MAX_DOCUMENT_BYTES = 2 * 1024 * 1024;

    private final String origin;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private final AtomicInteger generation = new AtomicInteger();

    public EngineDocumentClient(String origin) {
        this.origin = origin;
    }

    public void fetch(String sourcePath, int viewportWidth, Callback callback) {
        final int requestGeneration = generation.incrementAndGet();
        executor.execute(() -> {
            try {
                String endpoint = origin
                        + "/api/oap-engine/document?path="
                        + Uri.encode(sourcePath)
                        + "&viewport="
                        + Math.max(160, Math.min(2048, viewportWidth));
                HttpURLConnection connection = (HttpURLConnection) new URL(endpoint).openConnection();
                connection.setRequestMethod("GET");
                connection.setConnectTimeout(CONNECT_TIMEOUT_MS);
                connection.setReadTimeout(READ_TIMEOUT_MS);
                connection.setInstanceFollowRedirects(false);
                connection.setRequestProperty("Accept", "application/json");
                connection.setRequestProperty("X-OAP-Renderer-Request", "OAP_ENGINE_ANDROID");

                int status = connection.getResponseCode();
                if (status != 200) {
                    connection.disconnect();
                    postFallback(callback, sourcePath, requestGeneration);
                    return;
                }

                String renderer = connection.getHeaderField("X-OAP-Renderer");
                if (!"OAP_ENGINE".equals(renderer)) {
                    connection.disconnect();
                    postFallback(callback, sourcePath);
                    return;
                }

                String body;
                try (InputStream input = connection.getInputStream()) {
                    body = readBounded(input);
                } finally {
                    connection.disconnect();
                }

                mainHandler.post(() -> {
                    if (generation.get() == requestGeneration) {
                        callback.onEngineDocument(body, sourcePath);
                    }
                });
            } catch (IOException | RuntimeException error) {
                postFallback(callback, sourcePath);
            }
        });
    }

    private void postFallback(Callback callback, String sourcePath, int requestGeneration) {
        mainHandler.post(() -> {
            if (generation.get() == requestGeneration) {
                callback.onFallback(sourcePath);
            }
        });
    }

    private static String readBounded(InputStream input) throws IOException {
        StringBuilder builder = new StringBuilder();
        int total = 0;
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(input, StandardCharsets.UTF_8)
        )) {
            char[] buffer = new char[4096];
            int count;
            while ((count = reader.read(buffer)) != -1) {
                total += count;
                if (total > MAX_DOCUMENT_BYTES) {
                    throw new IOException("OAP Engine document too large");
                }
                builder.append(buffer, 0, count);
            }
        }
        return builder.toString();
    }

    public void close() {
        generation.incrementAndGet();
        executor.shutdownNow();
    }
}
