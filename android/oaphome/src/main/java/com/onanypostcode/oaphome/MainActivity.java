package com.onanypostcode.oaphome;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.ResolveInfo;
import android.content.pm.PackageManager;
import android.Manifest;
import android.view.MotionEvent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.provider.Settings;
import android.net.Uri;
import android.content.ActivityNotFoundException;
import android.view.WindowManager;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.EditText;
import android.text.TextWatcher;
import android.text.Editable;
import android.widget.FrameLayout;
import android.graphics.drawable.Drawable;
import java.text.DateFormat;
import java.util.Date;
import java.util.List;

public class MainActivity extends Activity {
    private static final int GOLD = Color.rgb(236, 188, 75);
    private static final String OAP_API_ORIGIN = "https://www.onanypostcode.com";
    private static final String PTT_CONTACTS_PATH = "/ptt/contacts";
    private static final int PTT_MIC_PERMISSION_REQUEST = 777;
    private boolean pttTransportReady = false;
    private boolean pttPressed = false;
    private TextView pttStateView;
    private LinearLayout body;
    private TextView clock;
    private TextView earth;
    private final android.os.Handler clockHandler = new android.os.Handler(android.os.Looper.getMainLooper());
    // Avoid an anonymous MainActivity$1 class in the on-device D8 build.
    // Keep the same minute cadence and lifecycle cancellation.
    private final Runnable clockTick = this::updateClock;

    private void updateClock() {
        if (clock != null) {
            clock.setText(DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.SHORT).format(new Date()));
            clockHandler.postDelayed(clockTick, 60000);
        }
    }

    private GradientDrawable panel() {
        GradientDrawable d = new GradientDrawable();
        d.setColor(Color.rgb(15, 18, 25));
        d.setCornerRadius(22);
        d.setStroke(2, GOLD);
        return d;
    }

    private TextView label(String value, int size) {
        TextView v = new TextView(this);
        v.setText(value);
        v.setTextColor(GOLD);
        v.setTextSize(size);
        v.setGravity(Gravity.CENTER);
        return v;
    }

    private Button button(String name, View.OnClickListener click) {
        Button b = new Button(this);
        b.setText(name);
        b.setAllCaps(false);
        b.setTextColor(GOLD);
        b.setBackground(panel());
        b.setOnClickListener(click);
        return b;
    }

    private void base(String title) {
        if (activeWebView != null) closeWebView();
        clockHandler.removeCallbacks(clockTick);
        clock = null;
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(3, 6, 14));
        root.setPadding(dp(12), dp(8), dp(12), dp(8));
        getWindow().setStatusBarColor(Color.rgb(3, 6, 14));
        getWindow().setNavigationBarColor(Color.BLACK);
        setContentView(root);
        TextView heading = label(title, 29);
        heading.setTypeface(Typeface.SERIF, Typeface.BOLD);
        root.addView(heading, new LinearLayout.LayoutParams(-1, dp(54)));
        ScrollView scroll = new ScrollView(this);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(body);
    }

    private void addButton(String text, View.OnClickListener click) {
        Button b = button(text, click);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(54));
        p.setMargins(0, dp(4), 0, dp(4));
        body.addView(b, p);
    }

    private void home() {
        base("♛ OAP HOME");
        body.addView(label("ON ANY POSTCODE", 21));
        body.addView(label("BORN LOCAL · BUILT GLOBAL", 13));
        earth = label("🌍  OAP WORLD  ·  EARTH IS OUR TURF", 17);
        earth.setTypeface(Typeface.SERIF, Typeface.BOLD);
        body.addView(earth, new LinearLayout.LayoutParams(-1, dp(64)));
        clock = label("", 26);
        body.addView(clock, new LinearLayout.LayoutParams(-1, dp(64)));
        clockTick.run();

        LinearLayout info = new LinearLayout(this);
        info.setOrientation(LinearLayout.HORIZONTAL);
        body.addView(info, new LinearLayout.LayoutParams(-1, dp(94)));
        String[] infoLabels = {"☀ WEATHER\\nNOT CONNECTED", "▣ NEXT EVENT\\nNOT CONNECTED", "🌐 WORLD CLOCK\\nNOT CONNECTED"};
        for (String title : infoLabels) {
            TextView tile = label(title.replace("\\n", "\n"), 12);
            tile.setBackground(panel());
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, -1, 1);
            lp.setMargins(dp(2), dp(2), dp(2), dp(2));
            info.addView(tile, lp);
        }

        EditText search = new EditText(this);
        search.setSingleLine(true);
        search.setImeOptions(android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH);
        search.setContentDescription("Search OAP destinations or enter a secure web address");
        search.setHint("⌕ Search apps, OAP or web...");
        search.setTextColor(Color.WHITE);
        search.setHintTextColor(Color.LTGRAY);
        search.setBackground(panel());
        search.setPadding(dp(14), 0, dp(14), 0);
        body.addView(search, new LinearLayout.LayoutParams(-1, dp(58)));
        search.setOnEditorActionListener((v, actionId, event) -> {
            String query = search.getText().toString().trim();
            if (query.isEmpty()) return true;
            if (query.startsWith("https://")) {
                openInternetAddress(query);
            } else if (query.startsWith("http://") || query.contains("://")) {
                android.widget.Toast.makeText(this, "Only HTTPS addresses allowed", android.widget.Toast.LENGTH_SHORT).show();
            } else {
                String normalized = query.toUpperCase(java.util.Locale.ROOT);
                String[] destinations = {"OAP WORLD", "LINK UP", "SIKA", "OAP MAPS", "OAP MAIL",
                        "OAP MARKET", "OAP TV", "OAP ARENA", "OAP LIBRARY"};
                boolean matched = false;
                for (String name : destinations) {
                    if (name.equals(normalized) || name.replace("OAP ", "").equals(normalized)) {
                        destination(name);
                        matched = true;
                        break;
                    }
                }
                if (!matched) allApps();
            }
            return true;
        });

        String[] destinations = {"OAP WORLD", "LINK UP", "SIKA", "OAP MAPS", "OAP MAIL",
                "OAP MARKET", "OAP TV", "OAP ARENA", "OAP LIBRARY"};
        String[] icons = {"🌍", "◉", "◈", "⌖", "✉", "▣", "▶", "♟", "▤"};
        String[] captions = {"ONE ECOSYSTEM", "PEOPLE & COMMUNITY", "FINANCE & OPPORTUNITY",
                "PLACES & NAVIGATION", "YOUR INBOX", "BUY · SELL · GROW",
                "WATCH & STREAM", "GAMES & CHALLENGES", "LEARN & EXPLORE"};
        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(3);
        body.addView(grid);
        int availableWidth = getResources().getDisplayMetrics().widthPixels - dp(32);
        int tileWidth = Math.max(dp(86), (availableWidth - dp(12)) / 3);
        for (int i = 0; i < destinations.length; i++) {
            final String name = destinations[i];
            Button tile = button(icons[i] + "\n" + name + "\n" + captions[i], v -> destination(name));
            tile.setTextSize(11);
            tile.setGravity(Gravity.CENTER);
            tile.setContentDescription(name + ". " + captions[i]);
            GridLayout.LayoutParams lp = new GridLayout.LayoutParams();
            lp.width = tileWidth;
            lp.height = dp(112);
            lp.setMargins(dp(2), dp(4), dp(2), dp(4));
            grid.addView(tile, lp);
        }
        TextView divider = label("────  ON ANY POSTCODE  ────", 13);
        divider.setPadding(0, dp(10), 0, dp(10));
        body.addView(divider);
        LinearLayout dock = new LinearLayout(this);
        dock.setOrientation(LinearLayout.HORIZONTAL);
        body.addView(dock, new LinearLayout.LayoutParams(-1, dp(82)));
        String[] dockLabels = {"☎\nPhone", "▣\nMessages", "◎\nInternet\nBEGORO-KORADASO", "◉\nCamera", "⌃\nAll Apps"};
        for (int i = 0; i < dockLabels.length; i++) {
            final int index = i;
            Button item = button(dockLabels[i], v -> {
                if (index == 0) open(new Intent(Intent.ACTION_DIAL));
                else if (index == 1) open(new Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:")));
                else if (index == 2) openInternet();
                else if (index == 3) open(new Intent("android.media.action.IMAGE_CAPTURE"));
                else allApps();
            });
            item.setTextSize(index == 2 ? 9 : 11);
            item.setContentDescription(dockLabels[i].replace("\n", " "));
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, -1, 1);
            lp.setMargins(dp(2), dp(3), dp(2), dp(3));
            dock.addView(item, lp);
        }
        addButton("⚙ SETTINGS", v -> startActivity(new Intent(Settings.ACTION_SETTINGS)));
        addButton("🎙 PTT", v -> pttMenu());
    }

    private void openInternetAddress(String url) {
        if (!safeWebAddress(Uri.parse(url))) {
            android.widget.Toast.makeText(this, "Only standard HTTPS pages allowed", android.widget.Toast.LENGTH_SHORT).show();
            return;
        }
        openInternet();
        if (activeWebView != null) activeWebView.loadUrl(url);
    }

    private int dp(int n) { return (int)(n * getResources().getDisplayMetrics().density + 0.5f); }

    private void quickApps() {
        base("QUICK APPS");
        addButton("PHONE", v -> open(new Intent(Intent.ACTION_DIAL)));
        addButton("MESSAGES", v -> open(new Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:"))));
        addButton("INTERNET", v -> openInternet());
        addButton("CAMERA", v -> open(new Intent("android.media.action.IMAGE_CAPTURE")));
        addButton("BACK", v -> home());
    }

    private void virtualAndroid() {
        base("OAP VIRTUAL ANDROID");
        body.addView(label("VIRTUAL DEVICE CONTROL", 19));
        body.addView(label("Runtime: NOT CONNECTED", 17));
        body.addView(label("No Android VM, remote session or virtual device has been provisioned.", 14));
        body.addView(label("OAP Home V2: local launcher source; virtual-device integration pending.", 14));
        addButton("OPEN OAP INTERNET", v -> openInternet());
        addButton("BACK TO OAP HOME", v -> home());
    }

    private android.webkit.WebView activeWebView;

    private boolean safeWebAddress(Uri uri) {
        return uri != null && "https".equalsIgnoreCase(uri.getScheme())
                && uri.getHost() != null && !uri.getHost().isEmpty()
                && uri.getUserInfo() == null && uri.getPort() == -1;
    }

    private void closeWebView() {
        if (activeWebView != null) {
            android.webkit.WebView old = activeWebView;
            activeWebView = null;
            old.stopLoading();
            old.loadUrl("about:blank");
            old.destroy();
        }
    }

    private void openInternet() {
        closeWebView();
        base("OAP INTERNET");
        body.addView(label("OAP INTERNET · IN-APP HTTPS VIEWER", 18));
        body.addView(label("Uses the device Android WebView provider, not an independent OAP browser engine. JavaScript and file access disabled.", 13));
        EditText address = new EditText(this);
        address.setSingleLine(true);
        address.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_VARIATION_URI);
        address.setHint("Enter HTTPS website");
        address.setText("https://www.onanypostcode.com");
        address.setTextColor(Color.WHITE);
        address.setHintTextColor(Color.LTGRAY);
        body.addView(address, new LinearLayout.LayoutParams(-1, dp(56)));
        android.webkit.WebView viewer = new android.webkit.WebView(this);
        activeWebView = viewer;
        android.webkit.WebSettings settings = viewer.getSettings();
        settings.setJavaScriptEnabled(false);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setDomStorageEnabled(false);
        settings.setMixedContentMode(android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setSupportMultipleWindows(false);
        settings.setGeolocationEnabled(false);
        settings.setSaveFormData(false);
        settings.setBlockNetworkImage(false);
        settings.setBlockNetworkLoads(false);
        viewer.setWebChromeClient(new android.webkit.WebChromeClient() {
            @Override public boolean onJsAlert(android.webkit.WebView view, String url, String message, android.webkit.JsResult result) {
                result.cancel();
                return true;
            }
            @Override public void onGeolocationPermissionsShowPrompt(String origin, android.webkit.GeolocationPermissions.Callback callback) {
                callback.invoke(origin, false, false);
            }
        });
        android.webkit.CookieManager.getInstance().setAcceptThirdPartyCookies(viewer, false);
        viewer.setWebViewClient(new android.webkit.WebViewClient() {
            @Override public void onReceivedSslError(android.webkit.WebView view, android.webkit.SslErrorHandler handler, android.net.http.SslError error) {
                handler.cancel();
                android.widget.Toast.makeText(MainActivity.this, "HTTPS certificate rejected", android.widget.Toast.LENGTH_SHORT).show();
            }
            @Override public android.webkit.WebResourceResponse shouldInterceptRequest(android.webkit.WebView view, android.webkit.WebResourceRequest request) {
                if (!"https".equalsIgnoreCase(request.getUrl().getScheme())) {
                    return new android.webkit.WebResourceResponse("text/plain", "UTF-8",
                            new java.io.ByteArrayInputStream(new byte[0]));
                }
                return super.shouldInterceptRequest(view, request);
            }
            @Override public boolean shouldOverrideUrlLoading(android.webkit.WebView view, android.webkit.WebResourceRequest request) {
                if (!request.isForMainFrame()) return false;
                if (!safeWebAddress(request.getUrl())) {
                    android.widget.Toast.makeText(MainActivity.this, "Only standard HTTPS pages allowed", android.widget.Toast.LENGTH_SHORT).show();
                    return true;
                }
                return false;
            }
        });
        addButton("OPEN HTTPS PAGE", v -> {
            Uri uri = Uri.parse(address.getText().toString().trim());
            if (!safeWebAddress(uri)) {
                android.widget.Toast.makeText(this, "Enter a standard HTTPS website", android.widget.Toast.LENGTH_SHORT).show();
                return;
            }
            viewer.loadUrl(uri.toString());
        });
        body.addView(viewer, new LinearLayout.LayoutParams(-1, dp(440)));
        addButton("BACK IN OAP INTERNET", v -> {
            if (activeWebView == viewer && viewer.canGoBack()) viewer.goBack();
        });
        addButton("FORWARD IN OAP INTERNET", v -> {
            if (activeWebView == viewer && viewer.canGoForward()) viewer.goForward();
        });
        addButton("RELOAD HTTPS PAGE", v -> {
            if (activeWebView == viewer && viewer.getUrl() != null
                    && safeWebAddress(Uri.parse(viewer.getUrl()))) viewer.reload();
        });
        addButton("BACK TO OAP HOME", v -> { closeWebView(); home(); });
    }

    private void open(Intent intent) {
        try { startActivity(intent); }
        catch (ActivityNotFoundException e) { destination("No compatible app installed"); }
    }

    private void pttMenu() {
        base("🎙 PTT");
        body.addView(label("OAP WORLD · PTT", 18));
        body.addView(label("Standalone push-to-talk · separate from The Link / Link Up", 13));

        TextView target = label("SELECTED · NONE", 17);
        target.setBackground(panel());
        target.setPadding(dp(8), dp(14), dp(8), dp(14));
        body.addView(target, new LinearLayout.LayoutParams(-1, dp(64)));

        pttStateView = label(pttTransportReady ? "READY · MIC OFF" : "LOCKED · MIC OFF", 19);
        pttStateView.setTypeface(Typeface.DEFAULT_BOLD);
        body.addView(pttStateView, new LinearLayout.LayoutParams(-1, dp(58)));

        Button talk = button("🎙  HOLD TO TALK", v -> { });
        talk.setEnabled(pttTransportReady);
        talk.setAlpha(pttTransportReady ? 1.0f : 0.55f);
        talk.setContentDescription(pttTransportReady
                ? "Hold to request microphone access and talk"
                : "Hold to talk locked until a Certified PTT contact or Room and live transport are connected");
        talk.setOnTouchListener((view, event) -> handlePttTouch(event));
        LinearLayout.LayoutParams talkLayout = new LinearLayout.LayoutParams(-1, dp(150));
        talkLayout.setMargins(0, dp(8), 0, dp(10));
        body.addView(talk, talkLayout);

        body.addView(label("Choose a Certified contact or Room first. Live device-to-device audio is not yet proven on this phone.", 13));

        GridLayout dock = new GridLayout(this);
        dock.setColumnCount(2);
        body.addView(dock);
        String[] items = {"CONTACTS", "ROOMS", "INCOMING", "HISTORY", "SETTINGS"};
        for (String item : items) {
            Button nav = button(item, v -> pttSection(item, pttStatusFor(item)));
            GridLayout.LayoutParams p = new GridLayout.LayoutParams();
            p.width = (getResources().getDisplayMetrics().widthPixels - dp(34)) / 2;
            p.height = dp(58);
            p.setMargins(dp(2), dp(3), dp(2), dp(3));
            dock.addView(nav, p);
        }
        addButton("BACK TO OAP HOME", v -> home());
    }

    private boolean handlePttTouch(MotionEvent event) {
        if (!pttTransportReady) {
            setPttState("LOCKED · MIC OFF");
            return true;
        }
        if (event.getAction() == MotionEvent.ACTION_DOWN) {
            pttPressed = true;
            if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                setPttState("MIC PERMISSION REQUIRED");
                requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, PTT_MIC_PERMISSION_REQUEST);
                return true;
            }
            setPttState("READY · MIC PERMITTED · TRANSPORT NOT CONNECTED");
            return true;
        }
        if (event.getAction() == MotionEvent.ACTION_UP || event.getAction() == MotionEvent.ACTION_CANCEL) {
            pttPressed = false;
            setPttState("READY · MIC OFF");
            return true;
        }
        return true;
    }

    private void setPttState(String value) {
        if (pttStateView != null) pttStateView.setText(value);
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != PTT_MIC_PERMISSION_REQUEST) return;
        boolean granted = grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED;
        pttPressed = false;
        setPttState(granted ? "READY · MIC OFF" : "LOCKED · MIC DENIED");
    }

    private String pttStatusFor(String title) {
        if ("CONTACTS".equals(title)) return "Certified Contacts endpoint: " + OAP_API_ORIGIN + PTT_CONTACTS_PATH + " · authenticated native session not connected yet.";
        if ("ROOMS".equals(title)) return "PTT Rooms are not connected to this launcher yet.";
        if ("INCOMING".equals(title)) return "Incoming PTT signalling is not connected to this launcher yet.";
        if ("HISTORY".equals(title)) return "PTT history is not connected to this launcher yet.";
        return "PTT permissions and transport settings are not connected to this launcher yet.";
    }

    private void pttSection(String title, String status) {
        base("PTT · " + title);
        body.addView(label(status, 16));
        body.addView(label("Nothing here is presented as live until the corresponding transport and device proof passes.", 12));
        addButton("BACK TO TALK", v -> pttMenu());
        addButton("BACK TO OAP HOME", v -> home());
    }

    private void destination(String name) {
        if ("PTT".equals(name)) {
            pttMenu();
            return;
        }
        base(name);
        body.addView(label("This destination is not connected yet.", 18));
        addButton("BACK TO OAP HOME", v -> home());
    }

    private void allApps() {
        base("ALL APPS");
        EditText search = new EditText(this);
        search.setSingleLine(true);
        search.setHint("Search installed apps");
        search.setHintTextColor(Color.LTGRAY);
        search.setTextColor(Color.WHITE);
        body.addView(search, new LinearLayout.LayoutParams(-1, dp(54)));
        LinearLayout results = new LinearLayout(this);
        results.setOrientation(LinearLayout.VERTICAL);
        body.addView(results);
        Intent intent = new Intent(Intent.ACTION_MAIN);
        intent.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> apps = getPackageManager().queryIntentActivities(intent, 0);
        apps.sort((a, b) -> a.loadLabel(getPackageManager()).toString()
                .compareToIgnoreCase(b.loadLabel(getPackageManager()).toString()));
        Runnable refresh = () -> {
            results.removeAllViews();
            String filter = search.getText().toString().trim().toLowerCase(java.util.Locale.ROOT);
            for (ResolveInfo app : apps) {
                String name = app.loadLabel(getPackageManager()).toString();
                if (!name.toLowerCase(java.util.Locale.ROOT).contains(filter)) continue;
                Button b = button(name, v -> {
                    Intent launch = getPackageManager().getLaunchIntentForPackage(app.activityInfo.packageName);
                    if (launch != null) open(launch);
                });
                Drawable icon = app.loadIcon(getPackageManager());
                if (icon != null) {
                    icon.setBounds(0, 0, dp(28), dp(28));
                    b.setCompoundDrawables(icon, null, null, null);
                    b.setCompoundDrawablePadding(dp(12));
                }
                LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(58));
                p.setMargins(0, dp(3), 0, dp(3));
                results.addView(b, p);
            }
        };
        search.addTextChangedListener(new TextWatcher() {
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            public void onTextChanged(CharSequence s, int start, int before, int count) { refresh.run(); }
            public void afterTextChanged(Editable e) {}
        });
        refresh.run();
        addButton("BACK TO OAP HOME", v -> home());
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        home();
    }

    @Override public void onBackPressed() {
        if (activeWebView != null && activeWebView.canGoBack()) {
            activeWebView.goBack();
        } else if (clock == null) {
            home();
        } else {
            super.onBackPressed();
        }
    }

    @Override protected void onDestroy() {
        closeWebView();
        clockHandler.removeCallbacks(clockTick);
        clock = null;
        super.onDestroy();
    }
}
