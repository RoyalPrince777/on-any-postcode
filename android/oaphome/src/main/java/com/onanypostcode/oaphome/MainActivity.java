package com.onanypostcode.oaphome;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        TextView view = new TextView(this);
        view.setText("OAP Home");
        view.setTextSize(28);
        view.setPadding(40, 80, 40, 40);
        setContentView(view);
    }
}
