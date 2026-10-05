package com.onanypostcode.oapworld;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.Uri;

import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.Map;

public final class EngineOriginStorage {
    private static final String STORE_NAME = "oap_engine_origin_storage_v1";
    private static final int ORIGIN_QUOTA_BYTES = 64 * 1024;
    private static final int MAX_KEYS_PER_ORIGIN = 256;
    private static final int MAX_KEY_BYTES = 256;
    private static final int MAX_VALUE_BYTES = 16 * 1024;

    private final SharedPreferences preferences;

    public EngineOriginStorage(Context context) {
        preferences = context.getSharedPreferences(STORE_NAME, Context.MODE_PRIVATE);
    }

    private static int bytes(String value) {
        return value.getBytes(StandardCharsets.UTF_8).length;
    }

    private static String origin(String rawUrl) {
        Uri uri = Uri.parse(rawUrl == null ? "" : rawUrl.trim());
        String scheme = uri.getScheme();
        String host = uri.getHost();
        if (scheme == null || host == null || uri.getUserInfo() != null) {
            throw new IllegalArgumentException("invalid_origin");
        }
        scheme = scheme.toLowerCase(Locale.ROOT);
        if (!"https".equals(scheme) && !"http".equals(scheme)) {
            throw new IllegalArgumentException("unsupported_origin_scheme");
        }
        int port = uri.getPort();
        if (port == -1) {
            port = "https".equals(scheme) ? 443 : 80;
        }
        return scheme + "://" + host.toLowerCase(Locale.ROOT) + ":" + port;
    }

    private static String prefix(String rawUrl) {
        return origin(rawUrl) + "|";
    }

    public synchronized String getItem(String rawUrl, String key) {
        String cleanKey = key == null ? "" : key;
        return preferences.getString(prefix(rawUrl) + cleanKey, null);
    }

    public synchronized void setItem(String rawUrl, String key, String value) {
        String cleanKey = key == null ? "" : key;
        String cleanValue = value == null ? "" : value;
        if (cleanKey.isEmpty() || bytes(cleanKey) > MAX_KEY_BYTES) {
            throw new IllegalArgumentException("invalid_storage_key");
        }
        if (bytes(cleanValue) > MAX_VALUE_BYTES) {
            throw new IllegalArgumentException("storage_value_too_large");
        }

        String prefix = prefix(rawUrl);
        String targetKey = prefix + cleanKey;
        Map<String, ?> all = preferences.getAll();
        int count = 0;
        int usage = 0;
        boolean exists = false;
        for (Map.Entry<String, ?> entry : all.entrySet()) {
            if (!entry.getKey().startsWith(prefix)) {
                continue;
            }
            count++;
            String storedKey = entry.getKey().substring(prefix.length());
            String storedValue = String.valueOf(entry.getValue());
            if (entry.getKey().equals(targetKey)) {
                exists = true;
                continue;
            }
            usage += bytes(storedKey) + bytes(storedValue);
        }
        if (!exists && count >= MAX_KEYS_PER_ORIGIN) {
            throw new IllegalStateException("storage_key_limit");
        }
        usage += bytes(cleanKey) + bytes(cleanValue);
        if (usage > ORIGIN_QUOTA_BYTES) {
            throw new IllegalStateException("origin_storage_quota_exceeded");
        }
        preferences.edit().putString(targetKey, cleanValue).apply();
    }

    public synchronized void removeItem(String rawUrl, String key) {
        String cleanKey = key == null ? "" : key;
        preferences.edit().remove(prefix(rawUrl) + cleanKey).apply();
    }

    public synchronized void clearOrigin(String rawUrl) {
        String prefix = prefix(rawUrl);
        SharedPreferences.Editor editor = preferences.edit();
        for (String key : preferences.getAll().keySet()) {
            if (key.startsWith(prefix)) {
                editor.remove(key);
            }
        }
        editor.apply();
    }
}
