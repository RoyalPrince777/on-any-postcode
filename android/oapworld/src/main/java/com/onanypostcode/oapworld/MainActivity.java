package com.onanypostcode.oapworld;

import android.annotation.SuppressLint;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.webkit.CookieManager;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;

import androidx.activity.ComponentActivity;

public final class MainActivity extends ComponentActivity {
    private static final String OAP_ORIGIN = "https://on-any-postcode.onrender.com";
    private WebView webView;
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
        root.addView(toolbar, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        ));
        root.addView(webView, new LinearLayout.LayoutParams(
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
        homeButton.setOnClickListener(v -> webView.loadUrl(OAP_ORIGIN + "/"));
        reloadButton.setOnClickListener(v -> webView.reload());
        goButton.setOnClickListener(v -> navigate(omnibox.getText().toString()));
        omnibox.setOnEditorActionListener((view, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_GO) {
                navigate(omnibox.getText().toString());
                return true;
            }
            return false;
        });

        if (state == null) {
            webView.loadUrl(OAP_ORIGIN + "/");
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
            webView.loadUrl(OAP_ORIGIN + input);
            return;
        }

        Uri parsed = Uri.parse(input);
        String scheme = parsed.getScheme();
        if ("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme)) {
            webView.loadUrl(input);
            return;
        }

        boolean looksLikeHost = !input.contains(" ")
                && input.contains(".")
                && !input.startsWith(".");
        if (looksLikeHost) {
            webView.loadUrl("https://" + input);
            return;
        }

        webView.loadUrl(OAP_ORIGIN + "/search?q=" + Uri.encode(input));
    }

    private void refreshNavigationState() {
        backButton.setEnabled(webView != null && webView.canGoBack());
        forwardButton.setEnabled(webView != null && webView.canGoForward());
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
