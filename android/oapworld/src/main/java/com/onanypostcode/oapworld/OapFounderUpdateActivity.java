package com.onanypostcode.oapworld;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Button;
import androidx.activity.ComponentActivity;

/**
 * Founder-controlled update entry. Read-only until a signed release and
 * independently verified install flow are available. Never downloads or
 * installs arbitrary packages.
 */
public final class OapFounderUpdateActivity extends ComponentActivity {
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(32, 40, 32, 32);
        layout.setBackgroundColor(0xff070b11);
        TextView heading = new TextView(this);
        heading.setText("OAP ANDROID · FOUNDER UPDATE CENTRE");
        heading.setTextColor(0xffffce70);
        heading.setTextSize(22);
        layout.addView(heading);
        TextView status = new TextView(this);
        status.setText("Manual updates only. No update has been downloaded or verified by this screen.\n\nCheck official OAP releases, verify signing and compatibility, then approve installation through Android.\n\nExisting data must be preserved; no silent installation.");
        status.setTextColor(0xffffffff);
        status.setTextSize(16);
        status.setPadding(0, 28, 0, 28);
        layout.addView(status);
        Button releases = new Button(this);
        releases.setText("View OAP releases");
        releases.setOnClickListener(v -> {
            Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(
                    "https://github.com/RoyalPrince777/on-any-postcode/releases"));
            if (i.resolveActivity(getPackageManager()) != null) startActivity(i);
        });
        layout.addView(releases);
        Button close = new Button(this);
        close.setText("Back to OAP Home");
        close.setOnClickListener(v -> finish());
        layout.addView(close);
        setContentView(layout);
    }
}
