package com.onanypostcode.oaphome;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.ResolveInfo;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.text.DateFormat;
import java.util.Date;
import java.util.List;

public class MainActivity extends Activity {
    private static final int GOLD = Color.rgb(236, 188, 75);
    private LinearLayout body;
    private TextView clock;

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
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(3, 6, 14));
        root.setPadding(18, 28, 18, 12);
        setContentView(root);
        TextView heading = label(title, 29);
        heading.setTypeface(Typeface.SERIF, Typeface.BOLD);
        root.addView(heading, new LinearLayout.LayoutParams(-1, 78));
        ScrollView scroll = new ScrollView(this);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(body);
    }

    private void addButton(String text, View.OnClickListener click) {
        Button b = button(text, click);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, 76);
        p.setMargins(0, 7, 0, 7);
        body.addView(b, p);
    }

    private void home() {
        base("♛ OAP HOME");
        body.addView(label("ON ANY POSTCODE", 18));
        body.addView(label("BORN LOCAL · BUILT GLOBAL", 13));
        clock = label("", 38);
        body.addView(clock, new LinearLayout.LayoutParams(-1, 110));
        updateClock();
        String[] destinations = {"OAP WORLD", "LINK UP", "SIKA", "OAP MAPS", "OAP MAIL",
                "OAP MARKET", "OAP TV", "OAP ARENA", "OAP LIBRARY"};
        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(3);
        body.addView(grid);
        for (String name : destinations) {
            Button b = button(name, v -> destination(name));
            GridLayout.LayoutParams p = new GridLayout.LayoutParams();
            p.width = getResources().getDisplayMetrics().widthPixels / 3 - 22;
            p.height = 105;
            p.setMargins(3, 5, 3, 5);
            grid.addView(b, p);
        }
        addButton("ALL APPS", v -> allApps());
        addButton("ANDROID SETTINGS", v -> startActivity(new Intent(Settings.ACTION_SETTINGS)));
    }

    private void updateClock() {
        if (clock == null) return;
        clock.setText(DateFormat.getDateTimeInstance(DateFormat.FULL, DateFormat.SHORT).format(new Date()));
        clock.postDelayed(() -> updateClock(), 60000);
    }

    private void destination(String name) {
        base(name);
        body.addView(label("This destination is not connected yet.", 18));
        addButton("BACK TO OAP HOME", v -> home());
    }

    private void allApps() {
        base("ALL APPS");
        Intent intent = new Intent(Intent.ACTION_MAIN);
        intent.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> apps = getPackageManager().queryIntentActivities(intent, 0);
        apps.sort((a, b) -> a.loadLabel(getPackageManager()).toString()
                .compareToIgnoreCase(b.loadLabel(getPackageManager()).toString()));
        for (ResolveInfo app : apps) {
            addButton(app.loadLabel(getPackageManager()).toString(), v -> {
                Intent launch = getPackageManager().getLaunchIntentForPackage(app.activityInfo.packageName);
                if (launch != null) startActivity(launch);
            });
        }
        addButton("BACK TO OAP HOME", v -> home());
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        home();
    }

    @Override public void onBackPressed() {
        home();
    }
}
