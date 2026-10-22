package com.onanypostcode.oapworld;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.text.format.DateFormat;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextClock;
import android.widget.TextView;

/** Native, independently installable Founder Home entry. Not an Android HOME replacement. */
public final class OapHomeActivity extends Activity {
    private static final String ORIGIN = "https://on-any-postcode.onrender.com";
    private static final int GOLD = Color.rgb(231, 184, 73);

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.rgb(6, 7, 10));
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(20, 28, 20, 28);
        scroll.addView(root);

        TextView heading = new TextView(this);
        heading.setText("♛  OAP HOME");
        heading.setTextColor(GOLD);
        heading.setTextSize(31);
        heading.setGravity(Gravity.CENTER);
        root.addView(heading);

        TextView subtitle = new TextView(this);
        subtitle.setText("ON ANY POSTCODE  ·  BORN LOCAL, BUILT GLOBAL");
        subtitle.setTextColor(Color.WHITE);
        subtitle.setGravity(Gravity.CENTER);
        root.addView(subtitle);

        TextClock clock = new TextClock(this);
        clock.setFormat24Hour("EEEE d MMMM    HH:mm");
        clock.setFormat12Hour("EEEE d MMMM    h:mm a");
        clock.setTextSize(26);
        clock.setTextColor(GOLD);
        clock.setGravity(Gravity.CENTER);
        clock.setPadding(0, 32, 0, 28);
        root.addView(clock);

        Button search = tile("SEARCH OAP");
        search.setOnClickListener(v -> open("/search"));
        root.addView(search);

        String[] names = {"OAP WORLD", "LINK UP", "SIKA", "OAP MAPS",
                "OAP MAIL", "OAP MARKET", "OAP TV", "OAP ARENA", "OAP LIBRARY"};
        String[] paths = {"/world", "/linkup", "/sika", "/maps",
                "/mail", "/market", "/tv", "/arena", "/library"};
        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(3);
        for (int i = 0; i < names.length; i++) {
            final String path = paths[i];
            Button button = tile(names[i]);
            button.setTextSize(12);
            GridLayout.LayoutParams params = new GridLayout.LayoutParams();
            params.width = 0;
            params.height = dp(108);
            params.columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f);
            params.setMargins(dp(3), dp(5), dp(3), dp(5));
            grid.addView(button, params);
            button.setOnClickListener(v -> open(path));
        }
        root.addView(grid);
        TextView notice = new TextView(this);
        notice.setText("OAP services open their existing web routes. Availability depends on the live service.");
        notice.setTextColor(Color.LTGRAY);
        notice.setPadding(4, 24, 4, 0);
        root.addView(notice);
        setContentView(scroll);
    }

    private int dp(int n) {
        return (int) (n * getResources().getDisplayMetrics().density + 0.5f);
    }

    private Button tile(String label) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        button.setTextColor(GOLD);
        button.setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.rgb(23, 24, 29)));
        button.setContentDescription("Open " + label);
        return button;
    }

    private void open(String path) {
        // Only compile-time first-party paths are accepted; no arbitrary external URL.
        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(ORIGIN + path));
        try {
            startActivity(intent);
        } catch (android.content.ActivityNotFoundException exception) {
            new android.app.AlertDialog.Builder(this)
                    .setMessage("No browser is available to open this OAP service.")
                    .setPositiveButton("OK", null).show();
        }
    }
}
