package com.onanypostcode.oaphome;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.ResolveInfo;
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
    private LinearLayout body;
    private TextView clock;
    private TextView earth;
    private final android.os.Handler clockHandler = new android.os.Handler(android.os.Looper.getMainLooper());
    private final Runnable clockTick = new Runnable() {
        @Override public void run() {
            if (clock != null && clock.isAttachedToWindow()) {
                clock.setText(DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.SHORT).format(new Date()));
                clockHandler.postDelayed(this, 60000);
            }
        }
    };
    private final android.os.Handler clockHandler = new android.os.Handler(android.os.Looper.getMainLooper());
    private final Runnable clockTick = new Runnable() {
        @Override public void run() {
            if (clock != null) {
                clock.setText(DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.SHORT).format(new Date()));
                clockHandler.postDelayed(this, 60000);
            }
        }
    };

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
        clockHandler.removeCallbacks(clockTick);
        clock = null;
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
        body.addView(label("ON ANY POSTCODE", 18));
        body.addView(label("BORN LOCAL · BUILT GLOBAL", 13));
        earth = label("◎  EARTH IS OUR TURF  ◎", 20);
        earth.setTypeface(Typeface.SERIF, Typeface.BOLD);
        body.addView(earth, new LinearLayout.LayoutParams(-1, dp(76)));
        clock = label("", 21);
        body.addView(clock, new LinearLayout.LayoutParams(-1, dp(60)));
        clockTick.run();
        String[] destinations = {"OAP WORLD", "LINK UP", "SIKA", "OAP MAPS", "OAP MAIL",
                "OAP MARKET", "OAP TV", "OAP ARENA", "OAP LIBRARY"};
        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(3);
        body.addView(grid);
        for (String name : destinations) {
            Button b = button(name, v -> destination(name));
            GridLayout.LayoutParams p = new GridLayout.LayoutParams();
            p.width = (getResources().getDisplayMetrics().widthPixels - dp(42)) / 3;
            p.height = dp(76);
            p.setMargins(dp(2), dp(4), dp(2), dp(4));
            grid.addView(b, p);
        }

        addButton("OAP INTERNET  ·  OPEN WEB", v -> openInternet());
        addButton("OAP VIRTUAL ANDROID  ·  STATUS", v -> virtualAndroid());
        addButton("SEARCH APPS", v -> allApps());
        addButton("ALL APPS", v -> allApps());
        addButton("PHONE  ·  MESSAGES  ·  INTERNET  ·  CAMERA", v -> quickApps());
        addButton("ANDROID SETTINGS", v -> startActivity(new Intent(Settings.ACTION_SETTINGS)));
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

    private void openInternet() {
        base("OAP INTERNET");
        body.addView(label("OAP INTERNET · WEB GATEWAY", 18));
        body.addView(label("Web access uses your installed browser. OAP browser engine is not connected.", 14));
        EditText address = new EditText(this);
        address.setSingleLine(true);
        address.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_VARIATION_URI);
        address.setHint("Enter HTTPS website");
        address.setText("https://www.onanypostcode.com");
        address.setTextColor(Color.WHITE);
        address.setHintTextColor(Color.LTGRAY);
        body.addView(address, new LinearLayout.LayoutParams(-1, dp(56)));
        addButton("OPEN WEBSITE", v -> {
            String raw = address.getText().toString().trim();
            Uri uri = Uri.parse(raw);
            if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost() == null || uri.getHost().isEmpty()
                    || uri.getUserInfo() != null) {
                android.widget.Toast.makeText(this, "Enter a valid HTTPS website", android.widget.Toast.LENGTH_SHORT).show();
                return;
            }
            open(new Intent(Intent.ACTION_VIEW, uri));
        });
        addButton("BACK TO OAP HOME", v -> home());
    }

    private void open(Intent intent) {
        try { startActivity(intent); }
        catch (ActivityNotFoundException e) { destination("No compatible app installed"); }
    }

    private void destination(String name) {
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
        if (clock == null) home();
        else super.onBackPressed();
    }

    @Override protected void onDestroy() {
        clockHandler.removeCallbacks(clockTick);
        clock = null;
        super.onDestroy();
    }
}
