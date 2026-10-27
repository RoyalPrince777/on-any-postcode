package com.onanypostcode.oapworld;

import android.annotation.SuppressLint;
import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
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
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageView;
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
    private TextView trustLabel;
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
        homeButton.setContentDescription("Return to OAP World");
        backButton.setContentDescription("Go back");

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
        toolbar.addView(
                omnibox,
                new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        );

        // Explicit touch target for navigation; keyboard action remains supported.
        Button goButton = navButton("Go");
        goButton.setContentDescription("Open the address entered in Koradaso Internet");
        goButton.setOnClickListener(v -> navigate(omnibox.getText().toString()));
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

        // KORADASO browser identity uses the original cropped royal artwork.
        // OAP World remains the homepage, not a second launcher.
        LinearLayout royalHeader = new LinearLayout(this);
        royalHeader.setOrientation(LinearLayout.HORIZONTAL);
        royalHeader.setGravity(Gravity.CENTER_VERTICAL);
        royalHeader.setPadding(dp(12), dp(6), dp(12), dp(6));
        royalHeader.setBackgroundColor(Color.rgb(8, 6, 12));

        ImageView royalIcon = new ImageView(this);
        royalIcon.setImageResource(R.drawable.koradaso_royal_icon);
        royalIcon.setContentDescription("KORADASO crown and K globe emblem");
        royalIcon.setScaleType(ImageView.ScaleType.FIT_CENTER);
        royalHeader.addView(royalIcon, new LinearLayout.LayoutParams(dp(48), dp(48)));

        LinearLayout brandText = new LinearLayout(this);
        brandText.setOrientation(LinearLayout.VERTICAL);
        brandText.setPadding(dp(8), 0, dp(6), 0);
        TextView brandName = new TextView(this);
        brandName.setText("KORADASO INTERNET");
        brandName.setTypeface(null, Typeface.BOLD);
        brandName.setTextColor(Color.rgb(239, 200, 93));
        brandName.setTextSize(14);
        brandName.setSingleLine(true);
        brandText.addView(brandName);
        TextView parentBrand = new TextView(this);
        parentBrand.setText("POWERED BY ON ANY POSTCODE");
        parentBrand.setTextColor(Color.rgb(195, 169, 216));
        parentBrand.setTextSize(9);
        parentBrand.setSingleLine(true);
        brandText.addView(parentBrand);
        royalHeader.addView(brandText, new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        trustLabel = new TextView(this);
        trustLabel.setText("OAP WORLD");
        trustLabel.setTextColor(Color.rgb(239, 200, 93));
        trustLabel.setTextSize(10);
        trustLabel.setContentDescription("Trust boundary: OAP WORLD");
        royalHeader.addView(trustLabel);
        root.addView(royalHeader, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
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
                Uri certified = Uri.parse(OAP_ORIGIN);
                boolean fromWorld = "https".equalsIgnoreCase(origin.getScheme())
                        && certified.getHost() != null
                        && certified.getHost().equalsIgnoreCase(origin.getHost())
                        && origin.getPort() == -1
                        && "/world".equals(origin.getPath());
                if (!fromWorld || message == null
                        || !message.startsWith("OPEN WEB — Leave OAP World and visit ")) {
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
            public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
                updateTrustLabel(url);
            }
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String scheme = uri.getScheme();
                return !("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme));
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                omnibox.setText(url);
                updateTrustLabel(url);
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
        homeButton.setOnClickListener(v -> openFirstPartyPath("/world"));
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
            openFirstPartyPath("/world");
        }
        refreshNavigationState();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
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
        engineClient.cancelPending();
        showWebViewFallback();
        updateTrustLabel(url);
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
            omnibox.setText(sourcePath == null ? "OAP Engine" : OAP_ORIGIN + sourcePath);
            updateTrustLabel(OAP_ORIGIN + (sourcePath == null ? "/world" : sourcePath));
            refreshNavigationState();
        } catch (org.json.JSONException error) {
            loadWebViewUrl(OAP_ORIGIN + (sourcePath == null ? "/" : sourcePath));
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
        if (engineFormBar != null) {
            engineFormBar.setVisibility(View.GONE);
        }
        if (webView != null) {
            webView.setVisibility(View.VISIBLE);
        }
        refreshNavigationState();
    }

    private void updateTrustLabel(String url) {
        if (trustLabel == null) {
            return;
        }
        Uri uri = Uri.parse(url == null ? "" : url);
        Uri owned = Uri.parse(OAP_ORIGIN);
        boolean firstParty = "https".equalsIgnoreCase(uri.getScheme())
                && owned.getHost() != null
                && owned.getHost().equalsIgnoreCase(uri.getHost())
                && uri.getPort() == -1
                && uri.getUserInfo() == null;
        String state = firstParty ? "OAP WORLD" : "OPEN WEB";
        trustLabel.setText(state);
        trustLabel.setTextColor(firstParty
                ? Color.rgb(239, 200, 93) : Color.rgb(255, 185, 117));
        trustLabel.setContentDescription("Trust boundary: " + state);
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
