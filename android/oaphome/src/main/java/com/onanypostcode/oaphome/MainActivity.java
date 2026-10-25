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
    // Native V2 only launches the existing Founder-authenticated SMI surface.
    // Never store, mirror or inject its credentials into the JS-disabled WebView.
    private static final String SMI_FOUNDER_PATH = "/mission/smi";
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

    private GradientDrawable royalHeader() {
        GradientDrawable d = new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{Color.rgb(4, 9, 22), Color.rgb(29, 23, 12), Color.rgb(5, 10, 23)});
        d.setCornerRadius(dp(18));
        d.setStroke(dp(1), GOLD);
        return d;
    }

    private GradientDrawable royalTile(int index) {
        // Native gradients keep every destination readable without remote image dependencies.
        final int[][] shades = {
                {0xFF17324B, 0xFF07101C}, {0xFF322143, 0xFF0C0B1D},
                {0xFF3A2A12, 0xFF110F0B}, {0xFF163C39, 0xFF08191A},
                {0xFF23334B, 0xFF0B111E}, {0xFF3B261B, 0xFF160D0B},
                {0xFF302348, 0xFF0C0A1D}, {0xFF243D27, 0xFF0A160C},
                {0xFF3A3030, 0xFF141014}
        };
        int[] colors = shades[Math.floorMod(index, shades.length)];
        GradientDrawable d = new GradientDrawable(GradientDrawable.Orientation.TL_BR, colors);
        d.setCornerRadius(dp(14));
        d.setStroke(dp(1), GOLD);
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
        scroll.setFillViewport(true);
        scroll.setClipToPadding(false);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(0, 0, 0, dp(28));
        scroll.addView(body);
        if ("♛ OAP ROYAL EMPIRE".equals(title)) {
            addPersistentHomeDock(root);
        }
    }

    private void addButton(String text, View.OnClickListener click) {
        Button b = button(text, click);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(54));
        p.setMargins(0, dp(4), 0, dp(4));
        body.addView(b, p);
    }

    private void home() {
        base("♛ OAP ROYAL EMPIRE");
        TextView royalBrand = label("♛  OAP ROYAL EMPIRE  ♛\nON ANY POSTCODE", 23);
        royalBrand.setTypeface(Typeface.SERIF, Typeface.BOLD);
        royalBrand.setBackground(royalHeader());
        body.addView(royalBrand, new LinearLayout.LayoutParams(-1, dp(96)));
        body.addView(label("BORN LOCAL · BUILT GLOBAL · EARTH IS OUR TURF", 12));
        earth = label("🌍  OAP WORLD", 17);
        earth.setTypeface(Typeface.SERIF, Typeface.BOLD);
        body.addView(earth, new LinearLayout.LayoutParams(-1, dp(64)));
        clock = label("", 30);
        clock.setTypeface(Typeface.SERIF, Typeface.BOLD);
        clock.setBackground(royalHeader());
        body.addView(clock, new LinearLayout.LayoutParams(-1, dp(68)));
        clockTick.run();

        Button smiQuick = button("🧠 SMI · CAPTAIN ALL IN\\nFOUNDER SIGN-IN REQUIRED", v -> openSmi());
        smiQuick.setTextSize(16);
        smiQuick.setGravity(Gravity.CENTER_VERTICAL);
        smiQuick.setContentDescription("Open Founder-only SMI Home in your Android browser. No credentials or media are transferred by OAP Home.");
        LinearLayout.LayoutParams smiQuickLayout = new LinearLayout.LayoutParams(-1, dp(72));
        smiQuickLayout.setMargins(0, dp(6), 0, dp(4));
        body.addView(smiQuick, smiQuickLayout);

        Button pttQuick = button("🎙 PTT\nSTANDALONE · MIC OFF", v -> openPttApp());
        pttQuick.setTextSize(16);
        pttQuick.setGravity(Gravity.CENTER_VERTICAL);
        pttQuick.setContentDescription("Open standalone PTT. Microphone stays off until you hold the talk control.");
        LinearLayout.LayoutParams pttQuickLayout = new LinearLayout.LayoutParams(-1, dp(72));
        pttQuickLayout.setMargins(0, dp(6), 0, dp(4));
        body.addView(pttQuick, pttQuickLayout);

        Button storeQuick = button("▣ OAP STORE\nINSTALL OAP APPS", v -> destination("OAP STORE"));
        storeQuick.setTextSize(14);
        storeQuick.setGravity(Gravity.CENTER_VERTICAL);
        storeQuick.setContentDescription("Open OAP Store to install first-party OAP apps into the phone and OAP Home app list.");
        LinearLayout.LayoutParams storeQuickLayout = new LinearLayout.LayoutParams(-1, dp(64));
        storeQuickLayout.setMargins(0, dp(4), 0, dp(8));
        body.addView(storeQuick, storeQuickLayout);

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
                String[] destinations = {"OAP WORLD", "OAP STORE", "LINK UP", "SIKA", "OAP MAPS", "OAP MAIL",
                        "OAP MARKET", "OAP TV", "OAP ARENA", "OAP LIBRARY"};
                boolean matched = false;
                if ("SMI".equals(normalized) || "CAPTAIN ALL IN".equals(normalized)
                        || "SOVEREIGN MEGAVERSE INTELLIGENCE".equals(normalized)) {
                    openSmi();
                    matched = true;
                } else if ("PTT".equals(normalized) || "PUSH TO TALK".equals(normalized)
                        || "PUSH-TO-TALK".equals(normalized)) {
                    openPttApp();
                    matched = true;
                } else {
                    for (String name : destinations) {
                        if (name.equals(normalized) || name.replace("OAP ", "").equals(normalized)) {
                            destination(name);
                            matched = true;
                            break;
                        }
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
        TextView destinationHeading = label("✦  EXPLORE YOUR WORLD  ✦", 15);
        destinationHeading.setTypeface(Typeface.SERIF, Typeface.BOLD);
        destinationHeading.setPadding(0, dp(12), 0, dp(5));
        body.addView(destinationHeading);
        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(3);
        body.addView(grid);
        // The root uses 12dp padding on each side; each tile adds 4dp margins.
        // Avoid a fixed minimum tile width that would overflow narrow screens.
        int availableWidth = getResources().getDisplayMetrics().widthPixels - dp(24);
        int tileWidth = Math.max(dp(1), (availableWidth - dp(12)) / 3);
        for (int i = 0; i < destinations.length; i++) {
            final String name = destinations[i];
            Button tile = button(icons[i] + "\n" + name + "\n" + captions[i], v -> destination(name));
            tile.setBackground(royalTile(i));
            tile.setTextSize(12);
            tile.setGravity(Gravity.CENTER);
            tile.setPadding(dp(3), dp(3), dp(3), dp(3));
            tile.setContentDescription(name + ". " + captions[i]);
            GridLayout.LayoutParams lp = new GridLayout.LayoutParams();
            lp.width = tileWidth;
            lp.height = dp(92);
            lp.setMargins(dp(2), dp(4), dp(2), dp(4));
            grid.addView(tile, lp);
        }
        TextView divider = label("────  ON ANY POSTCODE  ────", 13);
        divider.setPadding(0, dp(10), 0, dp(10));
        body.addView(divider);
        addButton("⚙ SETTINGS", v -> startActivity(new Intent(Settings.ACTION_SETTINGS)));
    }

    private void addPersistentHomeDock(LinearLayout root) {
        LinearLayout dock = new LinearLayout(this);
        dock.setOrientation(LinearLayout.HORIZONTAL);
        root.addView(dock, new LinearLayout.LayoutParams(-1, dp(64)));
        String[] dockLabels = {"☎\nPhone", "▣\nMessages", "◎\nInternet", "◉\nCamera", "⌃\nApps"};
        for (int i = 0; i < dockLabels.length; i++) {
            final int index = i;
            Button item = button(dockLabels[i], v -> {
                if (index == 0) open(new Intent(Intent.ACTION_DIAL));
                else if (index == 1) open(new Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:")));
                else if (index == 2) openInternet();
                else if (index == 3) open(new Intent("android.media.action.IMAGE_CAPTURE"));
                else allApps();
            });
            item.setTextSize(10);
            item.setAllCaps(false);
            item.setSingleLine(false);
            item.setMaxLines(2);
            item.setContentDescription(dockLabels[i].replace("\n", " "));
            item.setMinWidth(dp(48));
            item.setMinHeight(dp(48));
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, -1, 1);
            lp.setMargins(dp(2), dp(3), dp(2), dp(3));
            dock.addView(item, lp);
        }
    }

    private void openSmi() {
        // First-party Founder route only. Android's system browser owns login,
        // cookies, JavaScript and session lifecycle; the native launcher does not.
        Uri uri = Uri.parse(OAP_API_ORIGIN + SMI_FOUNDER_PATH);
        if (!safeWebAddress(uri)) {
            android.widget.Toast.makeText(this, "Secure SMI HTTPS route unavailable", android.widget.Toast.LENGTH_LONG).show();
            return;
        }
        try {
            Intent smi = new Intent(Intent.ACTION_VIEW, uri);
            smi.addCategory(Intent.CATEGORY_BROWSABLE);
            startActivity(smi);
        } catch (ActivityNotFoundException error) {
            android.widget.Toast.makeText(this, "A compatible Android browser is required for private SMI", android.widget.Toast.LENGTH_LONG).show();
        }
    }

    private void openPttApp() {
        Uri uri = Uri.parse(OAP_API_ORIGIN + "/ptt");
        try {
            Intent ptt = new Intent(Intent.ACTION_VIEW, uri);
            ptt.addCategory(Intent.CATEGORY_BROWSABLE);
            startActivity(ptt);
        } catch (ActivityNotFoundException error) {
            pttMenu();
        }
    }

    private void openInternetAddress(String url) {
        if (!safeWebAddress(Uri.parse(url))) {
            android.widget.Toast.makeText(this, "Only standard HTTPS pages allowed", android.widget.Toast.LENGTH_SHORT).show();
            return;
        }
        pendingInternetAddress = url;
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
        body.addView(label("OAP Royal Empire Home: local launcher source; virtual-device integration pending.", 14));
        addButton("OPEN OAP INTERNET", v -> openInternet());
        addButton("BACK TO ROYAL HOME", v -> home());
    }

    private android.webkit.WebView activeWebView;
    private String pendingInternetAddress;

    boolean safeWebAddress(Uri uri) {
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
        address.setText(pendingInternetAddress != null ? pendingInternetAddress : "https://www.onanypostcode.com");
        pendingInternetAddress = null;
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
        viewer.setWebChromeClient(new OapSecureChromeClient());
        android.webkit.CookieManager.getInstance().setAcceptThirdPartyCookies(viewer, false);
        TextView loadStatus = label("No page loaded", 12);
        body.addView(loadStatus);
        viewer.setWebViewClient(new OapSecureWebClient(this) {
            @Override public void onPageStarted(android.webkit.WebView view, String url, android.graphics.Bitmap favicon) {
                loadStatus.setText("Loading HTTPS page…");
            }
            @Override public void onPageFinished(android.webkit.WebView view, String url) {
                loadStatus.setText("Page loaded. Some interactive services require JavaScript, currently disabled for safety.");
            }
            @Override public void onReceivedError(android.webkit.WebView view, android.webkit.WebResourceRequest request,
                    android.webkit.WebResourceError error) {
                if (request.isForMainFrame()) loadStatus.setText("Page unavailable: " + error.getDescription());
            }
        });
        addButton("OPEN IN SYSTEM BROWSER (INTERACTIVE SITES)", v -> {
            Uri uri = Uri.parse(address.getText().toString().trim());
            if (!safeWebAddress(uri)) {
                android.widget.Toast.makeText(this, "Only standard HTTPS pages allowed", android.widget.Toast.LENGTH_SHORT).show();
                return;
            }
            try {
                Intent external = new Intent(Intent.ACTION_VIEW, uri);
                external.addCategory(Intent.CATEGORY_BROWSABLE);
                startActivity(external);
            } catch (ActivityNotFoundException error) {
                loadStatus.setText("No browser installed to open this page.");
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
        addButton("BACK TO ROYAL HOME", v -> { closeWebView(); home(); });
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
        addButton("BACK TO ROYAL HOME", v -> home());
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
        addButton("BACK TO ROYAL HOME", v -> home());
    }

    private void destination(String name) {
        if ("SMI".equals(name)) {
            openSmi();
            return;
        }
        if ("PTT".equals(name)) {
            openPttApp();
            return;
        }
        // Consolidated V2 navigation: open existing OAP routes rather than
        // displaying a dead-end placeholder. This does not certify service uptime.
        final String path;
        switch (name) {
            case "OAP WORLD": path = "/world"; break;
            case "OAP STORE": path = "/store"; break;
            case "LINK UP": path = "/linkup"; break;
            case "SIKA": path = "/sika"; break;
            case "OAP MAPS": path = "/maps"; break;
            case "OAP MAIL": path = "/mail"; break;
            case "OAP MARKET": path = "/market"; break;
            case "OAP TV": path = "/tv"; break;
            case "OAP ARENA": path = "/arena"; break;
            case "OAP LIBRARY": path = "/library"; break;
            default:
                base(name);
                body.addView(label("No verified OAP route for this destination.", 18));
                addButton("BACK TO ROYAL HOME", v -> home());
                return;
        }
        openInternetAddress(OAP_API_ORIGIN + path);
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
        search.addTextChangedListener(new OapAppSearchWatcher(refresh));
        refresh.run();
        addButton("BACK TO ROYAL HOME", v -> home());
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

// Named package-private callbacks avoid anonymous MainActivity$N classes in the
// phone-only D8 pipeline while retaining the existing fail-closed policies.
final class OapSecureChromeClient extends android.webkit.WebChromeClient {
    @Override public boolean onJsAlert(android.webkit.WebView view, String url, String message, android.webkit.JsResult result) {
        result.cancel();
        return true;
    }
    @Override public void onGeolocationPermissionsShowPrompt(String origin, android.webkit.GeolocationPermissions.Callback callback) {
        callback.invoke(origin, false, false);
    }
}

class OapSecureWebClient extends android.webkit.WebViewClient {
    private final MainActivity host;
    OapSecureWebClient(MainActivity host) { this.host = host; }
    @Override public void onReceivedSslError(android.webkit.WebView view, android.webkit.SslErrorHandler handler, android.net.http.SslError error) {
        handler.cancel();
        android.widget.Toast.makeText(host, "HTTPS certificate rejected", android.widget.Toast.LENGTH_SHORT).show();
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
        if (!host.safeWebAddress(request.getUrl())) {
            android.widget.Toast.makeText(host, "Only standard HTTPS pages allowed", android.widget.Toast.LENGTH_SHORT).show();
            return true;
        }
        return false;
    }
}

final class OapAppSearchWatcher implements TextWatcher {
    private final Runnable refresh;
    OapAppSearchWatcher(Runnable refresh) { this.refresh = refresh; }
    @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
    @Override public void onTextChanged(CharSequence s, int start, int before, int count) { refresh.run(); }
    @Override public void afterTextChanged(Editable e) {}
}
