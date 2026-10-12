package com.onanypostcode.oapworld;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.activity.ComponentActivity;

/** Founder-only manual update entry; never downloads or installs packages. */
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
        status.setText(localVersionSummary() +
                "\n\nRelease status: NOT CHECKED. No APK has been authenticated, downloaded or approved." +
                "\n\nUpdates remain manual. A newer release must be verified for package identity, " +
                "version, integrity, signing-key compatibility and governed approval before installation." +
                "\n\nThis screen never silently installs an APK.");
        status.setTextColor(0xffffffff);
        status.setTextSize(16);
        status.setPadding(0, 28, 0, 28);
        layout.addView(status);
        Button releases = new Button(this);
        releases.setText("View official OAP releases (external)");
        releases.setOnClickListener(v -> {
            Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(
                    "https://github.com/RoyalPrince777/on-any-postcode/releases"));
            try {
                startActivity(i);
            } catch (ActivityNotFoundException | SecurityException e) {
                status.setText(localVersionSummary() +
                        "\n\nCannot open releases: no permitted browser is available. No update was installed.");
            }
        });
        layout.addView(releases);
        Button close = new Button(this);
        close.setText("Back to OAP Home");
        close.setOnClickListener(v -> finish());
        layout.addView(close);
        setContentView(layout);
    }

    private String localVersionSummary() {
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            long versionCode = Build.VERSION.SDK_INT >= 28
                    ? info.getLongVersionCode() : info.versionCode;
            return "Installed package: " + getPackageName()
                    + "\nInstalled version: " + info.versionName
                    + "\nVersion code: " + versionCode;
        } catch (Exception e) {
            return "Installed version: UNKNOWN — local package metadata unavailable.";
        }
    }
}
