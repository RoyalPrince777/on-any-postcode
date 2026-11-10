package com.onanypostcode.oapworld;

import android.annotation.SuppressLint;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.Context;
import android.os.Environment;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.JsResult;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.URLUtil;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;

import androidx.activity.ComponentActivity;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public final class MainActivity extends ComponentActivity {
    private static final String OAP_ORIGIN = "https://onanypostcode.global";
    private static final String LOCAL_ORIGIN = "http://127.0.0.1:5050";
    private static final String KORADASO_TEST_ORIGIN = "http://127.0.0.1:5052";
    private String activeOrigin = KORADASO_TEST_ORIGIN;
    private Button modeButton;
    private WebView webView;
    private OapEngineView engineView;
    private EngineDocumentClient engineClient;
    private ScrollView engineScrollView;
    private LinearLayout engineNativeHost;
    private LinearLayout engineFormBar;
    private EditText engineSearchInput;
    private Button engineSearchButton;
    private boolean engineActive;
    private String engineSourcePath;
    private EditText omnibox;
    private Button backButton;
    private final List<String> engineHistory = new ArrayList<>();
    private int engineHistoryIndex = -1;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(5, 8, 7));

        LinearLayout toolbar = new LinearLayout(this);
        toolbar.setOrientation(LinearLayout.HORIZONTAL);
        toolbar.setGravity(Gravity.CENTER_VERTICAL);
        toolbar.setPadding(8, 8, 8, 8);

        backButton = navButton("‹");
        Button homeButton = navButton("OAP");
        modeButton = navButton("Local 5052");

        omnibox = new EditText(this);
        omnibox.setSingleLine(true);
        omnibox.setHint("Search OAP or enter web address");
        omnibox.setTextColor(Color.WHITE);
        omnibox.setHintTextColor(Color.rgb(150, 170, 158));
        omnibox.setBackgroundColor(Color.rgb(11, 23, 16));
        omnibox.setPadding(18, 10, 18, 10);
        omnibox.setImeOptions(EditorInfo.IME_ACTION_GO);
        omnibox.setInputType(
                android.text.InputType.TYPE_CLASS_TEXT
                        | android.text.InputType.TYPE_TEXT_VARIATION_URI
        );

        toolbar.addView(backButton);
        toolbar.addView(homeButton);
        toolbar.addView(modeButton);
        toolbar.addView(
                omnibox,
                new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        );

        webView = new WebView(this);
        engineClient = new EngineDocumentClient(activeOrigin);
        engineView = new OapEngineView(this);
        engineView.setLinkListener(this::navigate);
        engineScrollView = new ScrollView(this);
        engineScrollView.setFillViewport(true);
        engineScrollView.addView(engineView, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        ));

        engineFormBar = new LinearLayout(this);
        engineFormBar.setOrientation(LinearLayout.HORIZONTAL);
        engineFormBar.setGravity(Gravity.CENTER_VERTICAL);
        engineFormBar.setPadding(12, 8, 12, 8);
        engineFormBar.setVisibility(View.GONE);

        engineSearchInput = new EditText(this);
        engineSearchInput.setSingleLine(true);
        engineSearchInput.setHint("Search OAP");
        engineSearchInput.setTextColor(Color.WHITE);
        engineSearchInput.setHintTextColor(Color.rgb(150, 170, 158));
        engineSearchInput.setImeOptions(EditorInfo.IME_ACTION_SEARCH);
        engineSearchInput.setInputType(android.text.InputType.TYPE_CLASS_TEXT);

        engineSearchButton = navButton("Search");
        engineFormBar.addView(
                engineSearchInput,
                new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        );
        engineFormBar.addView(engineSearchButton);

        engineNativeHost = new LinearLayout(this);
        engineNativeHost.setOrientation(LinearLayout.VERTICAL);
        engineNativeHost.setVisibility(View.GONE);
        engineNativeHost.addView(
                engineFormBar,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT
                )
        );
        engineNativeHost.addView(
                engineScrollView,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        0,
                        1f
                )
        );

        FrameLayout renderHost = new FrameLayout(this);
        renderHost.addView(webView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
        ));
        renderHost.addView(engineNativeHost, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
        ));

        root.addView(toolbar, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        ));
        root.addView(renderHost, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                0,
                1f
        ));
        setContentView(root);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setSafeBrowsingEnabled(true);
        settings.setGeolocationEnabled(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setSupportMultipleWindows(false);
        settings.setUserAgentString(
                settings.getUserAgentString() + " OAPBrowser/1.0"
        );

        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        cookieManager.setAcceptThirdPartyCookies(webView, false);

        // WebView does not guarantee a visible JavaScript confirm dialog without a
        // WebChromeClient. Honour only the OAP World OPEN WEB trust boundary.
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onJsConfirm(WebView view, String url, String message, JsResult result) {
                Uri origin = Uri.parse(url == null ? "" : url);
                Uri certified = Uri.parse(activeOrigin);
                boolean sameTrustedOrigin = certified.getScheme() != null
                        && certified.getScheme().equalsIgnoreCase(origin.getScheme())
                        && certified.getHost() != null
                        && certified.getHost().equalsIgnoreCase(origin.getHost())
                        && origin.getPort() == certified.getPort();
                boolean worldConsent = "/world".equals(origin.getPath())
                        && message != null
                        && message.startsWith("OPEN WEB — Leave OAP World and visit ");
                boolean koradasoConsent = "/koradaso".equals(origin.getPath())
                        && message != null
                        && (message.startsWith("OPEN WEB — ")
                            || message.startsWith("OPEN WEB SEARCH — "));
                if (!sameTrustedOrigin || !(worldConsent || koradasoConsent)) {
                    result.cancel();
                    return true;
                }
                new AlertDialog.Builder(MainActivity.this)
                        .setTitle("OPEN WEB — External website")
                        .setMessage(message)
                        .setPositiveButton("Continue", (dialog, which) -> result.confirm())
                        .setNegativeButton("Stay in OAP World", (dialog, which) -> result.cancel())
                        .setOnCancelListener(dialog -> result.cancel())
                        .show();
                return true;
            }
        });

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String scheme = uri.getScheme();
                return !("https".equalsIgnoreCase(scheme) || isLocalLoopback(uri));
            }

            @Override
            public void onReceivedHttpError(
                    WebView view,
                    WebResourceRequest request,
                    WebResourceResponse response
            ) {
                if (request.isForMainFrame()
                        && response.getStatusCode() == 404
                        && (activeOrigin + "/koradaso").equals(request.getUrl().toString())) {
                    loadWebViewUrl(activeOrigin + "/world?source=oap-os");
                }
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                omnibox.setText(url);
                refreshNavigationState();
            }
        });

        // Explicit, user-confirmed downloads. Do not forward cookies or page credentials.
        // Android DownloadManager owns transfers; no OAP traffic proxy or storage permission.
        webView.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) -> {
            Uri target = Uri.parse(url == null ? "" : url);
            if (!"https".equalsIgnoreCase(target.getScheme())
                    || target.getHost() == null
                    || target.getHost().isEmpty()
                    || target.getUserInfo() != null) {
                new AlertDialog.Builder(MainActivity.this)
                        .setTitle("Download unavailable")
                        .setMessage("KORADASO only accepts direct HTTPS file downloads.")
                        .setPositiveButton("OK", (dialog, which) -> {})
                        .show();
                return;
            }
            String hostname = target.getHost();
            new AlertDialog.Builder(MainActivity.this)
                    .setTitle("Download file?")
                    .setMessage("Download from " + hostname + " to Android Downloads?")
                    .setPositiveButton("Download", (dialog, which) -> {
                        try {
                            DownloadManager.Request request = new DownloadManager.Request(target);
                            request.setTitle(URLUtil.guessFileName(url, contentDisposition, mimeType));
                            request.setMimeType(mimeType == null || mimeType.isEmpty()
                                    ? "application/octet-stream" : mimeType);
                            request.setNotificationVisibility(
                                    DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                            request.setDestinationInExternalPublicDir(
                                    Environment.DIRECTORY_DOWNLOADS,
                                    URLUtil.guessFileName(url, contentDisposition, mimeType));
                            DownloadManager manager =
                                    (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
                            if (manager == null) {
                                throw new IllegalStateException("download_manager_unavailable");
                            }
                            manager.enqueue(request);
                        } catch (RuntimeException error) {
                            new AlertDialog.Builder(MainActivity.this)
                                    .setTitle("Download not started")
                                    .setMessage("Android could not start this download.")
                                    .setPositiveButton("OK", (closed, ignored) -> {})
                                    .show();
                        }
                    })
                    .setNegativeButton("Cancel", (dialog, which) -> {})
                    .show();
        });

        backButton.setOnClickListener(v -> {
            if (engineActive && engineHistoryIndex > 0) {
                engineHistoryIndex--;
                openFirstPartyPath(engineHistory.get(engineHistoryIndex), false);
            } else if (!engineActive && webView.canGoBack()) {
                webView.goBack();
            }
        });
        homeButton.setOnClickListener(v -> loadWebViewUrl(activeOrigin + "/world?source=oap-os"));
        modeButton.setOnClickListener(v -> switchOrigin());
        engineSearchButton.setOnClickListener(v -> submitNativeSearch());
        engineSearchInput.setOnEditorActionListener((view, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                submitNativeSearch();
                return true;
            }
            return false;
        });
        omnibox.setOnEditorActionListener((view, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_GO) {
                navigate(omnibox.getText().toString());
                return true;
            }
            return false;
        });

        if (state == null) {
            openFirstPartyPath("/koradaso");
        }
        refreshNavigationState();
    }

    private static boolean isLocalLoopback(Uri uri) {
        return "http".equalsIgnoreCase(uri.getScheme())
                && "127.0.0.1".equals(uri.getHost())
                && (uri.getPort() == 5050 || uri.getPort() == 5052)
                && uri.getUserInfo() == null;
    }

    private void switchOrigin() {
        engineClient.cancelPending();
        engineClient.close();
        if (KORADASO_TEST_ORIGIN.equals(activeOrigin)) {
            activeOrigin = LOCAL_ORIGIN;
        } else if (LOCAL_ORIGIN.equals(activeOrigin)) {
            activeOrigin = OAP_ORIGIN;
        } else {
            activeOrigin = KORADASO_TEST_ORIGIN;
        }
        engineClient = new EngineDocumentClient(activeOrigin);
        engineHistory.clear();
        engineHistoryIndex = -1;
        modeButton.setText(LOCAL_ORIGIN.equals(activeOrigin) ? "Local 5050"
                : KORADASO_TEST_ORIGIN.equals(activeOrigin) ? "Local 5052" : "Online");
        openFirstPartyPath("/koradaso");
    }

    private Button navButton(String label) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        button.setMinWidth(0);
        button.setMinimumWidth(0);
        return button;
    }

    private void navigate(String rawInput) {
        String input = rawInput == null ? "" : rawInput.trim();
        if (input.isEmpty()) {
            return;
        }

        if (input.startsWith("/")) {
            openFirstPartyPath(input);
            return;
        }

        Uri parsed = Uri.parse(input);
        String scheme = parsed.getScheme();
        if ("https".equalsIgnoreCase(scheme) || isLocalLoopback(parsed)) {
            Uri oapOrigin = Uri.parse(activeOrigin);
            boolean sameOrigin = oapOrigin.getScheme().equalsIgnoreCase(parsed.getScheme())
                    && oapOrigin.getHost() != null
                    && oapOrigin.getHost().equalsIgnoreCase(parsed.getHost())
                    && parsed.getPort() == oapOrigin.getPort()
                    && parsed.getUserInfo() == null;
            if (sameOrigin) {
                String path = parsed.getEncodedPath();
                if (path == null || path.isEmpty()) {
                    path = "/";
                }
                String query = parsed.getEncodedQuery();
                openFirstPartyPath(query == null ? path : path + "?" + query);
            } else {
                loadWebViewUrl(input);
            }
            return;
        }

        boolean looksLikeHost = !input.contains(" ")
                && input.contains(".")
                && !input.startsWith(".");
        if (looksLikeHost) {
            loadWebViewUrl("https://" + input);
            return;
        }

        openFirstPartyPath("/search?q=" + Uri.encode(input));
    }

    private void openFirstPartyPath(String sourcePath) {
        openFirstPartyPath(sourcePath, true);
    }

    private void openFirstPartyPath(String sourcePath, boolean recordHistory) {
        final String path = sourcePath == null || sourcePath.isEmpty() ? "/" : sourcePath;
        int viewportWidth = engineScrollView != null && engineScrollView.getWidth() > 0
                ? engineScrollView.getWidth()
                : getResources().getDisplayMetrics().widthPixels;
        engineClient.fetch(path, viewportWidth, new EngineDocumentClient.Callback() {
            @Override
            public void onEngineDocument(String json, String resolvedPath) {
                showOapEngineDocument(json, resolvedPath, recordHistory);
            }

            @Override
            public void onFallback(String resolvedPath) {
                loadWebViewUrl(activeOrigin + resolvedPath);
            }
        });
    }

    private void loadWebViewUrl(String url) {
        engineClient.cancelPending();
        showWebViewFallback();
        Uri destination = Uri.parse(url);
        if (!"https".equalsIgnoreCase(destination.getScheme())
                && !isLocalLoopback(destination)) {
            return;
        }
        webView.loadUrl(url);
    }

    void showOapEngineDocument(String displayListJson, String sourcePath) {
        showOapEngineDocument(displayListJson, sourcePath, true);
    }

    private void showOapEngineDocument(
            String displayListJson,
            String sourcePath,
            boolean recordHistory
    ) {
        try {
            engineView.setDisplayListJson(displayListJson);
            configureNativeSearchForm(displayListJson);
            engineScrollView.scrollTo(0, 0);
            engineNativeHost.setVisibility(View.VISIBLE);
            webView.setVisibility(View.GONE);
            engineActive = true;
            engineSourcePath = sourcePath;
            if (recordHistory && sourcePath != null) {
                while (engineHistory.size() > engineHistoryIndex + 1) {
                    engineHistory.remove(engineHistory.size() - 1);
                }
                if (engineHistoryIndex < 0
                        || !sourcePath.equals(engineHistory.get(engineHistoryIndex))) {
                    engineHistory.add(sourcePath);
                    engineHistoryIndex = engineHistory.size() - 1;
                }
            }
            omnibox.setText(sourcePath == null ? "OAP Engine" : activeOrigin + sourcePath);
            refreshNavigationState();
        } catch (org.json.JSONException error) {
            loadWebViewUrl(activeOrigin + (sourcePath == null ? "/" : sourcePath));
        }
    }

    private void configureNativeSearchForm(String displayListJson) throws JSONException {
        engineFormBar.setVisibility(View.GONE);
        engineSearchInput.setText("");

        JSONObject document = new JSONObject(displayListJson);
        JSONArray forms = document.optJSONArray("forms");
        if (forms == null || forms.length() != 1) {
            return;
        }
        JSONObject form = forms.optJSONObject(0);
        if (form == null
                || !"GET".equals(form.optString("method"))
                || !form.optBoolean("same_origin_action", false)) {
            return;
        }

        Uri action = Uri.parse(form.optString("action", ""));
        Uri oapOrigin = Uri.parse(activeOrigin);
        boolean certifiedAction = oapOrigin.getScheme().equalsIgnoreCase(action.getScheme())
                && oapOrigin.getHost() != null
                && oapOrigin.getHost().equalsIgnoreCase(action.getHost())
                && action.getPort() == oapOrigin.getPort()
                && "/search".equals(action.getPath())
                && action.getQuery() == null
                && action.getFragment() == null;
        if (!certifiedAction) {
            return;
        }

        JSONArray controls = form.optJSONArray("controls");
        if (controls == null) {
            return;
        }
        boolean foundQuery = false;
        for (int index = 0; index < controls.length(); index++) {
            JSONObject control = controls.optJSONObject(index);
            if (control == null) {
                continue;
            }
            String name = control.optString("name", "");
            String type = control.optString("control_type", "").toLowerCase();
            if ("q".equals(name)
                    && !control.optBoolean("disabled", false)
                    && ("text".equals(type) || "search".equals(type))) {
                engineSearchInput.setText(control.optString("value", ""));
                foundQuery = true;
                break;
            }
        }
        if (foundQuery) {
            engineFormBar.setVisibility(View.VISIBLE);
        }
    }

    private void submitNativeSearch() {
        if (!engineActive || engineFormBar.getVisibility() != View.VISIBLE) {
            return;
        }
        String query = engineSearchInput.getText().toString().trim();
        if (query.length() > 120) {
            return;
        }
        int viewportWidth = engineScrollView != null && engineScrollView.getWidth() > 0
                ? engineScrollView.getWidth()
                : getResources().getDisplayMetrics().widthPixels;
        engineClient.submitCertifiedSearch(query, viewportWidth, new EngineDocumentClient.Callback() {
            @Override
            public void onEngineDocument(String json, String resolvedPath) {
                showOapEngineDocument(json, resolvedPath, true);
            }

            @Override
            public void onFallback(String resolvedPath) {
                loadWebViewUrl(activeOrigin + resolvedPath);
            }
        });
    }

    private void showWebViewFallback() {
        engineActive = false;
        engineSourcePath = null;
        if (engineNativeHost != null) {
            engineNativeHost.setVisibility(View.GONE);
        }
        if (engineFormBar != null) {
            engineFormBar.setVisibility(View.GONE);
        }
        if (webView != null) {
            webView.setVisibility(View.VISIBLE);
        }
        refreshNavigationState();
    }

    private void refreshNavigationState() {
        if (engineActive) {
            backButton.setEnabled(engineHistoryIndex > 0);
            return;
        }
        backButton.setEnabled(webView != null && webView.canGoBack());
    }

    @Override
    public void onBackPressed() {
        if (engineActive && engineHistoryIndex > 0) {
            engineHistoryIndex--;
            openFirstPartyPath(engineHistory.get(engineHistoryIndex), false);
        } else if (engineActive) {
            // At the native root there is no previous page: leave the Activity,
            // rather than exposing a blank or stale WebView fallback.
            super.onBackPressed();
        } else if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (engineClient != null) {
            engineClient.close();
        }
        super.onDestroy();
    }
}
