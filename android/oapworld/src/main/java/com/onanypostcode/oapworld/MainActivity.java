package com.onanypostcode.oapworld;

import android.annotation.SuppressLint;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.webkit.CookieManager;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import androidx.activity.ComponentActivity;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public final class MainActivity extends ComponentActivity {
    private static final String OAP_ORIGIN = "https://on-any-postcode.onrender.com";
    private static final String OAP_WORLD_PATH = "/world";
    private WebView webView;
    private OapEngineView engineView;
    private EngineDocumentClient engineClient;
    private ScrollView engineScrollView;
    private LinearLayout engineNativeHost;
    private boolean engineActive;
    private boolean certifiedSearchFormActive;
    private String engineSourcePath;
    private EditText omnibox;
    private Button backButton;
    private Button worldButton;
    private TextView trustState;
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
        worldButton = navButton("OAP World");

        trustState = new TextView(this);
        trustState.setText("OAP WORLD");
        trustState.setTextColor(Color.rgb(185, 206, 194));
        trustState.setGravity(Gravity.CENTER_VERTICAL);
        trustState.setPadding(10, 0, 10, 0);

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
        toolbar.addView(worldButton);
        toolbar.addView(
                omnibox,
                new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        );
        toolbar.addView(trustState);

        webView = new WebView(this);
        engineClient = new EngineDocumentClient(OAP_ORIGIN);
        engineView = new OapEngineView(this);
        engineView.setLinkListener(this::navigate);
        engineScrollView = new ScrollView(this);
        engineScrollView.setFillViewport(true);
        engineScrollView.addView(engineView, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        ));

        engineNativeHost = new LinearLayout(this);
        engineNativeHost.setOrientation(LinearLayout.VERTICAL);
        engineNativeHost.setVisibility(View.GONE);
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

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String scheme = uri.getScheme();
                return !("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme));
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                omnibox.setText(isOapUrl(url) ? "" : url);
                updateTrustState(url);
                refreshNavigationState();
            }
        });

        backButton.setOnClickListener(v -> {
            if (engineActive && engineHistoryIndex > 0) {
                engineHistoryIndex--;
                openFirstPartyPath(engineHistory.get(engineHistoryIndex), false);
            } else if (!engineActive && webView.canGoBack()) {
                webView.goBack();
            }
        });
        worldButton.setOnClickListener(v -> openFirstPartyPath(OAP_WORLD_PATH));
        omnibox.setOnEditorActionListener((view, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_GO
                    || actionId == EditorInfo.IME_ACTION_SEARCH) {
                String input = omnibox.getText().toString();
                if (certifiedSearchFormActive && !looksLikeWebAddress(input)) {
                    submitCertifiedSearchFromOmnibox(input);
                } else {
                    navigate(input);
                }
                return true;
            }
            return false;
        });

        if (state == null) {
            openFirstPartyPath(OAP_WORLD_PATH);
        }
        refreshNavigationState();
    }

    private Button navButton(String label) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        button.setMinWidth(0);
        button.setMinimumWidth(0);
        return button;
    }

    private boolean looksLikeWebAddress(String rawInput) {
        String input = rawInput == null ? "" : rawInput.trim();
        if (input.isEmpty()) {
            return false;
        }
        Uri parsed = Uri.parse(input);
        String scheme = parsed.getScheme();
        if ("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme)) {
            return true;
        }
        return !input.contains(" ") && input.contains(".") && !input.startsWith(".");
    }

    private boolean isOapUrl(String rawUrl) {
        if (rawUrl == null || rawUrl.isEmpty()) {
            return false;
        }
        Uri uri = Uri.parse(rawUrl);
        Uri oapOrigin = Uri.parse(OAP_ORIGIN);
        return "https".equalsIgnoreCase(uri.getScheme())
                && oapOrigin.getHost() != null
                && oapOrigin.getHost().equalsIgnoreCase(uri.getHost())
                && uri.getPort() == -1;
    }

    private void updateTrustState(String rawUrl) {
        trustState.setText(isOapUrl(rawUrl) ? "OAP WORLD" : "OPEN WEB");
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
        if ("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme)) {
            Uri oapOrigin = Uri.parse(OAP_ORIGIN);
            boolean sameOrigin = "https".equalsIgnoreCase(parsed.getScheme())
                    && oapOrigin.getHost() != null
                    && oapOrigin.getHost().equalsIgnoreCase(parsed.getHost())
                    && parsed.getPort() == -1;
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

        if (looksLikeWebAddress(input)) {
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
                loadWebViewUrl(OAP_ORIGIN + resolvedPath);
            }
        });
    }

    private void loadWebViewUrl(String url) {
        showWebViewFallback();
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
            updateTrustState(OAP_ORIGIN + (sourcePath == null ? OAP_WORLD_PATH : sourcePath));
            if (!certifiedSearchFormActive) {
                omnibox.setText("");
            }
            refreshNavigationState();
        } catch (org.json.JSONException error) {
            loadWebViewUrl(OAP_ORIGIN + (sourcePath == null ? "/" : sourcePath));
        }
    }

    private void configureNativeSearchForm(String displayListJson) throws JSONException {
        certifiedSearchFormActive = false;

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
        Uri oapOrigin = Uri.parse(OAP_ORIGIN);
        boolean certifiedAction = "https".equalsIgnoreCase(action.getScheme())
                && oapOrigin.getHost() != null
                && oapOrigin.getHost().equalsIgnoreCase(action.getHost())
                && action.getPort() == -1
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
                certifiedSearchFormActive = true;
                omnibox.setText(control.optString("value", ""));
                omnibox.setSelection(omnibox.getText().length());
                return;
            }
        }
    }

    private void submitCertifiedSearchFromOmnibox(String rawQuery) {
        if (!engineActive || !certifiedSearchFormActive) {
            return;
        }
        String query = rawQuery == null ? "" : rawQuery.trim();
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
                loadWebViewUrl(OAP_ORIGIN + resolvedPath);
            }
        });
    }

    private void showWebViewFallback() {
        engineActive = false;
        engineSourcePath = null;
        if (engineNativeHost != null) {
            engineNativeHost.setVisibility(View.GONE);
        }
        certifiedSearchFormActive = false;
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
            showWebViewFallback();
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
