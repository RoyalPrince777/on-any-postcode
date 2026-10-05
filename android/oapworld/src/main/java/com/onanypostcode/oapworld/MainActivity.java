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

import androidx.activity.ComponentActivity;

public final class MainActivity extends ComponentActivity {
    private static final String OAP_ORIGIN = "https://on-any-postcode.onrender.com";
    private WebView webView;
    private OapEngineView engineView;
    private EngineDocumentClient engineClient;
    private ScrollView engineScrollView;
    private boolean engineActive;
    private String engineSourcePath;
    private EditText omnibox;
    private Button backButton;
    private Button forwardButton;

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
        forwardButton = navButton("›");
        Button homeButton = navButton("OAP");
        Button reloadButton = navButton("↻");
        Button goButton = navButton("Go");

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
        toolbar.addView(forwardButton);
        toolbar.addView(homeButton);
        toolbar.addView(reloadButton);
        toolbar.addView(
                omnibox,
                new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        );
        toolbar.addView(goButton);

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
        engineScrollView.setVisibility(View.GONE);

        FrameLayout renderHost = new FrameLayout(this);
        renderHost.addView(webView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
        ));
        renderHost.addView(engineScrollView, new FrameLayout.LayoutParams(
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
                omnibox.setText(url);
                refreshNavigationState();
            }
        });

        backButton.setOnClickListener(v -> {
            if (webView.canGoBack()) {
                webView.goBack();
            }
        });
        forwardButton.setOnClickListener(v -> {
            if (webView.canGoForward()) {
                webView.goForward();
            }
        });
        homeButton.setOnClickListener(v -> openFirstPartyPath("/"));
        reloadButton.setOnClickListener(v -> {
            if (engineActive && engineSourcePath != null) {
                openFirstPartyPath(engineSourcePath);
            } else {
                webView.reload();
            }
        });
        goButton.setOnClickListener(v -> navigate(omnibox.getText().toString()));
        omnibox.setOnEditorActionListener((view, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_GO) {
                navigate(omnibox.getText().toString());
                return true;
            }
            return false;
        });

        if (state == null) {
            openFirstPartyPath("/");
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
        final String path = sourcePath == null || sourcePath.isEmpty() ? "/" : sourcePath;
        int viewportWidth = engineScrollView != null && engineScrollView.getWidth() > 0
                ? engineScrollView.getWidth()
                : getResources().getDisplayMetrics().widthPixels;
        engineClient.fetch(path, viewportWidth, new EngineDocumentClient.Callback() {
            @Override
            public void onEngineDocument(String json, String resolvedPath) {
                showOapEngineDocument(json, resolvedPath);
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
        try {
            engineView.setDisplayListJson(displayListJson);
            engineScrollView.scrollTo(0, 0);
            engineScrollView.setVisibility(View.VISIBLE);
            webView.setVisibility(View.GONE);
            engineActive = true;
            engineSourcePath = sourcePath;
            omnibox.setText(sourcePath == null ? "OAP Engine" : OAP_ORIGIN + sourcePath);
            refreshNavigationState();
        } catch (org.json.JSONException error) {
            loadWebViewUrl(OAP_ORIGIN + (sourcePath == null ? "/" : sourcePath));
        }
    }

    private void showWebViewFallback() {
        engineActive = false;
        engineSourcePath = null;
        if (engineScrollView != null) {
            engineScrollView.setVisibility(View.GONE);
        }
        if (webView != null) {
            webView.setVisibility(View.VISIBLE);
        }
        refreshNavigationState();
    }

    private void refreshNavigationState() {
        backButton.setEnabled(!engineActive && webView != null && webView.canGoBack());
        forwardButton.setEnabled(!engineActive && webView != null && webView.canGoForward());
    }

    @Override
    public void onBackPressed() {
        if (engineActive) {
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
