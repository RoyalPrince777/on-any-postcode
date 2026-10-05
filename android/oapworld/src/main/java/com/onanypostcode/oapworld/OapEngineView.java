package com.onanypostcode.oapworld;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.net.Uri;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public final class OapEngineView extends View {
    public interface LinkListener {
        void onSafeLink(String href);
    }

    private static final int CONTRACT_VERSION = 1;
    private static final int MAX_ITEMS = 5000;
    private static final int MAX_TEXT_LENGTH = 8192;
    private static final int MAX_ACCESSIBILITY_SUMMARY_NODES = 50;
    private static final int MAX_ACCESSIBILITY_SUMMARY_CHARS = 4096;

    private static final class Item {
        final String kind;
        final String text;
        final float x;
        final float y;
        final float width;
        final float height;
        final String href;
        final String color;
        final String backgroundColor;
        final boolean bold;
        final String src;

        Item(
                String kind,
                String text,
                float x,
                float y,
                float width,
                float height,
                String href,
                String color,
                String backgroundColor,
                boolean bold,
                String src
        ) {
            this.kind = kind;
            this.text = text;
            this.x = x;
            this.y = y;
            this.width = width;
            this.height = height;
            this.href = href;
            this.color = color;
            this.backgroundColor = backgroundColor;
            this.bold = bold;
            this.src = src;
        }
    }

    private final Paint textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint backgroundPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final List<Item> items = new ArrayList<>();
    private int documentWidth = 390;
    private int documentHeight = 1;
    private LinkListener linkListener;

    public OapEngineView(Context context) {
        super(context);
        initialize();
    }

    public OapEngineView(Context context, AttributeSet attrs) {
        super(context, attrs);
        initialize();
    }

    private void initialize() {
        setBackgroundColor(Color.rgb(5, 8, 7));
        textPaint.setColor(Color.WHITE);
        textPaint.setTextSize(16f);
        setFocusable(true);
        setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);
    }

    public void setLinkListener(LinkListener listener) {
        linkListener = listener;
    }

    public void clearDocument() {
        items.clear();
        documentWidth = 390;
        documentHeight = 1;
        setContentDescription(null);
        requestLayout();
        invalidate();
    }

    public void setDisplayListJson(String rawJson) throws JSONException {
        JSONObject document = new JSONObject(rawJson);
        if (!"OAP_ENGINE".equals(document.optString("engine"))) {
            throw new JSONException("not an OAP Engine document");
        }
        if (document.optInt("contract_version", -1) != CONTRACT_VERSION) {
            throw new JSONException("unsupported OAP Engine contract version");
        }

        int width = document.optInt("width", 0);
        int height = document.optInt("height", 0);
        if (width < 160 || width > 4096 || height < 1 || height > 200000) {
            throw new JSONException("invalid OAP Engine document geometry");
        }

        JSONArray rawItems = document.optJSONArray("items");
        if (rawItems == null || rawItems.length() > MAX_ITEMS) {
            throw new JSONException("invalid OAP Engine item count");
        }

        List<Item> parsed = new ArrayList<>();
        for (int index = 0; index < rawItems.length(); index++) {
            JSONObject rawItem = rawItems.getJSONObject(index);
            String kind = rawItem.optString("kind", "text");
            if (!"text".equals(kind) && !"link".equals(kind) && !"image".equals(kind)) {
                throw new JSONException("unsupported display item kind");
            }

            String text = rawItem.optString("text", "");
            if (text.length() > MAX_TEXT_LENGTH) {
                throw new JSONException("display item text too large");
            }

            float x = (float) rawItem.optDouble("x", -1);
            float y = (float) rawItem.optDouble("y", -1);
            float itemWidth = (float) rawItem.optDouble("width", -1);
            float itemHeight = (float) rawItem.optDouble("height", -1);
            if (x < 0 || y < 0 || itemWidth < 0 || itemHeight <= 0) {
                throw new JSONException("invalid display item geometry");
            }

            String href = rawItem.isNull("href") ? null : rawItem.optString("href", null);
            if (href != null && !isSafeHttpLink(href)) {
                throw new JSONException("unsafe display-list link scheme");
            }
            String color = safeHexColor(rawItem.optString("color", null));
            String backgroundColor = safeHexColor(rawItem.optString("background_color", null));
            boolean bold = rawItem.optBoolean("bold", false);
            String src = rawItem.isNull("src") ? null : rawItem.optString("src", null);
            if (src != null && !isSafeHttpLink(src)) {
                throw new JSONException("unsafe image source scheme");
            }
            parsed.add(
                    new Item(
                            kind,
                            text,
                            x,
                            y,
                            itemWidth,
                            itemHeight,
                            href,
                            color,
                            backgroundColor,
                            bold,
                            src
                    )
            );
        }

        items.clear();
        items.addAll(parsed);
        documentWidth = width;
        documentHeight = height;
        setContentDescription(accessibilitySummary(document.optJSONArray("accessibility")));
        requestLayout();
        invalidate();
    }

    private static String accessibilitySummary(JSONArray nodes) {
        if (nodes == null) {
            return null;
        }
        StringBuilder summary = new StringBuilder();
        int count = Math.min(nodes.length(), MAX_ACCESSIBILITY_SUMMARY_NODES);
        for (int index = 0; index < count; index++) {
            JSONObject node = nodes.optJSONObject(index);
            if (node == null) {
                continue;
            }
            String name = node.optString("name", "").trim();
            if (name.isEmpty()) {
                continue;
            }
            String role = node.optString("role", "").trim();
            String part = role.isEmpty() ? name : role + ": " + name;
            int remaining = MAX_ACCESSIBILITY_SUMMARY_CHARS - summary.length();
            if (remaining <= 0) {
                break;
            }
            if (summary.length() > 0) {
                summary.append(". ");
                remaining -= 2;
            }
            if (remaining <= 0) {
                break;
            }
            summary.append(part, 0, Math.min(part.length(), remaining));
        }
        return summary.length() == 0 ? null : summary.toString();
    }

    private static String safeHexColor(String value) {
        if (value == null || !value.matches("^#[0-9A-Fa-f]{6}$")) {
            return null;
        }
        return value.toUpperCase();
    }

    private static boolean isSafeHttpLink(String href) {
        Uri uri = Uri.parse(href);
        String scheme = uri.getScheme();
        return "https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme);
    }

    private float scale() {
        if (getWidth() <= 0 || documentWidth <= 0) {
            return 1f;
        }
        return (float) getWidth() / (float) documentWidth;
    }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        int measuredWidth = MeasureSpec.getSize(widthMeasureSpec);
        if (measuredWidth <= 0) {
            measuredWidth = documentWidth;
        }
        float scale = (float) measuredWidth / (float) Math.max(1, documentWidth);
        int desiredHeight = Math.max(1, Math.round(documentHeight * scale));
        setMeasuredDimension(
                resolveSize(measuredWidth, widthMeasureSpec),
                resolveSize(desiredHeight, heightMeasureSpec)
        );
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float scale = scale();
        canvas.save();
        canvas.scale(scale, scale);
        for (Item item : items) {
            if ("image".equals(item.kind)) {
                backgroundPaint.setColor(
                        item.backgroundColor != null
                                ? Color.parseColor(item.backgroundColor)
                                : Color.rgb(18, 28, 23)
                );
                canvas.drawRect(
                        item.x,
                        item.y,
                        item.x + item.width,
                        item.y + item.height,
                        backgroundPaint
                );
                textPaint.setColor(
                        item.color != null
                                ? Color.parseColor(item.color)
                                : Color.rgb(190, 205, 196)
                );
                textPaint.setFakeBoldText(false);
                textPaint.setTextSize(14f);
                canvas.drawText(
                        item.text,
                        item.x + 8f,
                        item.y + Math.min(item.height - 8f, 24f),
                        textPaint
                );
                continue;
            }
            if (item.backgroundColor != null) {
                backgroundPaint.setColor(Color.parseColor(item.backgroundColor));
                canvas.drawRect(
                        item.x,
                        item.y,
                        item.x + item.width,
                        item.y + item.height,
                        backgroundPaint
                );
            }
            if (item.color != null) {
                textPaint.setColor(Color.parseColor(item.color));
            } else {
                textPaint.setColor("link".equals(item.kind)
                        ? Color.rgb(105, 190, 255)
                        : Color.WHITE);
            }
            textPaint.setFakeBoldText(item.bold);
            float fontSize = Math.max(8f, item.height - 8f);
            textPaint.setTextSize(fontSize);
            canvas.drawText(item.text, item.x, item.y + item.height - 6f, textPaint);
        }
        canvas.restore();
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (event.getAction() != MotionEvent.ACTION_UP || linkListener == null) {
            return true;
        }
        float scale = scale();
        float x = event.getX() / scale;
        float y = event.getY() / scale;
        for (Item item : items) {
            if (item.href == null) {
                continue;
            }
            boolean inside = x >= item.x && x <= item.x + item.width
                    && y >= item.y && y <= item.y + item.height;
            if (inside) {
                linkListener.onSafeLink(item.href);
                return true;
            }
        }
        return true;
    }
}
