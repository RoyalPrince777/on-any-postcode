package com.onanypostcode.oapworld;

import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import androidx.activity.ComponentActivity;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** Founder-first native entry. Not registered as Android's default HOME. */
public final class OapHomeActivity extends ComponentActivity {
    private static final int GOLD = Color.rgb(235, 184, 73);
    private static final int BG = Color.rgb(5, 8, 15);
    private LinearLayout root;
    private int dp(int n) { return Math.round(getResources().getDisplayMetrics().density * n); }

    private GradientDrawable panel(int color, int radius) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(color);
        d.setCornerRadius(dp(radius));
        d.setStroke(dp(1), GOLD);
        return d;
    }

    private TextView label(String text, int size, int color) {
        TextView v = new TextView(this);
        v.setText(text); v.setTextColor(color); v.setTextSize(size);
        v.setGravity(Gravity.CENTER); v.setPadding(dp(5), dp(9), dp(5), dp(9));
        return v;
    }

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackground(new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{Color.rgb(5,8,15), Color.rgb(20,20,26), Color.rgb(7,8,13)}));
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(16), dp(16), dp(16), dp(24));
        scroll.addView(root);
        setContentView(scroll);

        TextView brand = label("♛  OAP", 43, GOLD);
        root.addView(brand);
        root.addView(label("ON ANY POSTCODE  ·  HOME", 17, GOLD));
        root.addView(label("BORN LOCAL. BUILT GLOBAL.", 12, Color.WHITE));
        root.addView(label(new SimpleDateFormat("EEEE d MMMM", Locale.getDefault())
                .format(new Date()).toUpperCase(Locale.getDefault()), 15, Color.WHITE));
        TextView clock = label(new SimpleDateFormat("HH:mm", Locale.getDefault())
                .format(new Date()), 43, GOLD);
        root.addView(clock);
        clock.postDelayed(new Runnable() {
            @Override public void run() {
                clock.setText(new SimpleDateFormat("HH:mm", Locale.getDefault()).format(new Date()));
                clock.postDelayed(this, 30000);
            }
        }, 30000);

        // Live weather and calendar data are deliberately not fabricated.
        TextView widgets = label("☀ Weather: connect with permission    ·    ▦ Calendar: connect with permission", 12, Color.WHITE);
        widgets.setBackground(panel(Color.rgb(17,22,31), 14));
        root.addView(widgets);

        EditText search = new EditText(this);
        search.setSingleLine(true);
        search.setHint("⌕  Search apps, OAP or web…");
        search.setHintTextColor(Color.LTGRAY);
        search.setTextColor(Color.WHITE);
        search.setPadding(dp(16), dp(12), dp(16), dp(12));
        search.setBackground(panel(Color.rgb(14,18,29), 18));
        search.setImeOptions(EditorInfo.IME_ACTION_SEARCH);
        LinearLayout.LayoutParams searchParams = new LinearLayout.LayoutParams(-1, -2);
        searchParams.setMargins(0, dp(16), 0, dp(12));
        root.addView(search, searchParams);
        search.setOnEditorActionListener((v, action, event) -> {
            if (action == EditorInfo.IME_ACTION_SEARCH) {
                String q = search.getText().toString().trim();
                if (!q.isEmpty()) openPath("/search?q=" + Uri.encode(q));
                return true;
            }
            return false;
        });

        String[][] tiles = {
                {"◎", "OAP WORLD", "ONE ECOSYSTEM", "/world"},
                {"☏", "LINK UP", "PEOPLE & COMMUNITY", "/linkup"},
                {"◉", "SIKA", "FINANCE & OPPORTUNITY", "/sika"},
                {"⌖", "OAP MAPS", "PLACES & NAVIGATION", "/oap-map"},
                {"✉", "OAP MAIL", "YOUR INBOX", "/mail"},
                {"▣", "OAP MARKET", "BUY · SELL · GROW", "/market"},
                {"▶", "OAP TV", "WATCH & STREAM", "/tv"},
                {"♟", "OAP ARENA", "GAMES & CHALLENGES", "/arena"},
                {"▤", "OAP LIBRARY", "LEARN & EXPLORE", "/library/books"}
        };
        for (int row = 0; row < 3; row++) {
            LinearLayout line = new LinearLayout(this);
            line.setOrientation(LinearLayout.HORIZONTAL);
            LinearLayout.LayoutParams rowParams = new LinearLayout.LayoutParams(-1, dp(125));
            rowParams.bottomMargin = dp(10);
            root.addView(line, rowParams);
            for (int col = 0; col < 3; col++) {
                String[] item = tiles[row * 3 + col];
                LinearLayout tile = new LinearLayout(this);
                tile.setGravity(Gravity.CENTER);
                tile.setOrientation(LinearLayout.VERTICAL);
                tile.setBackground(panel(Color.rgb(13,17,27), 16));
                tile.addView(label(item[0], 30, GOLD));
                tile.addView(label(item[1], 12, GOLD));
                tile.setContentDescription(item[1] + ", " + item[2]);
                tile.setOnClickListener(v -> openPath(item[3]));
                LinearLayout.LayoutParams tileParams = new LinearLayout.LayoutParams(0, -1, 1f);
                tileParams.setMargins(dp(3), 0, dp(3), 0);
                line.addView(tile, tileParams);
            }
        }
        root.addView(label("O N   A N Y   P O S T C O D E", 12, GOLD));
        LinearLayout dock = new LinearLayout(this);
        dock.setGravity(Gravity.CENTER);
        root.addView(dock);
        addDock(dock, "☎\nPhone", () -> openSystem(Intent.ACTION_DIAL));
        addDock(dock, "✉\nMessages", () -> openSystem(Intent.ACTION_SENDTO, Uri.parse("smsto:")));
        addDock(dock, "◎\nInternet", () -> openPath("/world"));
        addDock(dock, "◉\nCamera", () -> openSystem("android.media.action.IMAGE_CAPTURE"));
        addDock(dock, "⌃\nAll Apps", () -> new android.app.AlertDialog.Builder(this)
                .setTitle("OAP HOME")
                .setItems(new String[]{"Android Home Settings", "Return to Phone Home"},
                        (dialog, which) -> {
                            if (which == 0) openSystem(Settings.ACTION_HOME_SETTINGS);
                            else {
                                Intent home = new Intent(Intent.ACTION_MAIN);
                                home.addCategory(Intent.CATEGORY_HOME);
                                home.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                                startActivity(home);
                                finish();
                            }
                        }).show());
    }

    private void addDock(LinearLayout row, String text, Runnable action) {
        TextView button = label(text, 12, Color.WHITE);
        button.setBackground(panel(Color.rgb(15,20,31), 14));
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, dp(68), 1f);
        p.setMargins(dp(2), 0, dp(2), 0);
        row.addView(button, p);
        button.setOnClickListener(v -> action.run());
    }
    private void openPath(String path) {
        Intent intent = new Intent(this, MainActivity.class);
        intent.putExtra("oap_start_path", path);
        startActivity(intent);
    }
    private void openSystem(String action) { openSystem(action, null); }
    private void openSystem(String action, Uri data) {
        Intent intent = new Intent(action);
        if (data != null) intent.setData(data);
        if (intent.resolveActivity(getPackageManager()) != null) startActivity(intent);
        else new android.app.AlertDialog.Builder(this)
                .setMessage("No compatible application available.")
                .setPositiveButton("OK", null).show();
    }
}
