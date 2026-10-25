package com.onanypostcode.oaphome;

import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.ColorFilter;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.RadialGradient;
import android.graphics.RectF;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;

/**
 * Local Android Canvas artwork for the Founder-approved royal Home V2 direction.
 * No network, browser renderer, image permission, wallpaper access or telemetry.
 */
final class RoyalHomeArt {
    private static final int GOLD = 0xFFF3C76A;
    private static final int GLOW = 0xFFFFE2A1;

    private RoyalHomeArt() { }

    private abstract static class Art extends Drawable {
        final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        int alpha = 255;
        @Override public void setAlpha(int value) { alpha = value; invalidateSelf(); }
        @Override public void setColorFilter(ColorFilter value) { p.setColorFilter(value); invalidateSelf(); }
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
        void fill(Canvas c, int color, float left, float top, float right, float bottom) {
            p.setStyle(Paint.Style.FILL); p.setShader(null); p.setColor(color);
            c.drawRect(left, top, right, bottom, p);
        }
        void line(Canvas c, int color, float width, float x1, float y1, float x2, float y2) {
            p.setStyle(Paint.Style.STROKE); p.setShader(null);
            p.setColor(color); p.setStrokeWidth(width); p.setStrokeCap(Paint.Cap.ROUND);
            c.drawLine(x1, y1, x2, y2, p);
            p.setStyle(Paint.Style.FILL);
        }
        void oval(Canvas c, int color, float left, float top, float right, float bottom) {
            p.setStyle(Paint.Style.FILL); p.setShader(null); p.setColor(color);
            c.drawOval(left, top, right, bottom, p);
        }
        void circle(Canvas c, int color, float x, float y, float r) {
            p.setStyle(Paint.Style.FILL); p.setShader(null); p.setColor(color);
            c.drawCircle(x, y, r, p);
        }
    }

    /** Gold-lit Earth artwork drawn entirely by Android Canvas. */
    static final class EarthBackdrop extends Art {
        @Override public void draw(Canvas original) {
            android.graphics.Rect bounds = getBounds();
            int saved = original.save();
            original.translate(bounds.left, bounds.top);
            float w = Math.max(1, bounds.width());
            float h = Math.max(1, bounds.height());
            original.scale(w / 400f, h / 230f);
            Canvas c = original;
            p.setColor(Color.WHITE);
            p.setShader(new LinearGradient(0, 0, 400, 230,
                    new int[]{0xFF040510, 0xFF101629, 0xFF170E12}, null, Shader.TileMode.CLAMP));
            c.drawRect(0, 0, 400, 230, p);
            p.setShader(null);

            for (int i = 0; i < 105; i++) {
                float x = (i * 127 + 19) % 400;
                float y = (i * i * 43 + 7) % 215;
                circle(c, i % 4 == 0 ? 0xA6FFE2A1 : 0x669DBADF, x, y, i % 7 == 0 ? 1.25f : .6f);
            }

            // Planet is clipped locally: no remote images and no wallpaper permission.
            Path globe = new Path();
            globe.addCircle(268, 237, 206, Path.Direction.CW);
            int clipped = c.save();
            c.clipPath(globe);
            p.setColor(Color.WHITE);
            p.setShader(new RadialGradient(208, 130, 260,
                    new int[]{0xFF24425A, 0xFF0C1C2B, 0xFF050914},
                    new float[]{0, .52f, 1}, Shader.TileMode.CLAMP));
            c.drawCircle(268, 237, 206, p); p.setShader(null);

            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(1.3f); p.setColor(0x447B8C96);
            for (int i = 0; i < 6; i++)
                c.drawOval(new RectF(90 + i * 18, 44, 446 - i * 18, 424), p);
            p.setStyle(Paint.Style.FILL);

            Path europe = new Path();
            europe.moveTo(179, 98); europe.lineTo(194, 83); europe.lineTo(211, 90);
            europe.lineTo(227, 80); europe.lineTo(246, 99); europe.lineTo(238, 119);
            europe.lineTo(266, 138); europe.lineTo(244, 156); europe.lineTo(227, 146);
            europe.lineTo(206, 157); europe.lineTo(190, 139); europe.close();
            p.setColor(0x99795526); c.drawPath(europe, p);
            Path africa = new Path();
            africa.moveTo(224, 151); africa.lineTo(255, 143); africa.lineTo(273, 168);
            africa.lineTo(263, 198); africa.lineTo(240, 224); africa.lineTo(215, 198);
            africa.lineTo(203, 173); africa.close();
            c.drawPath(africa, p);
            Path asia = new Path();
            asia.moveTo(251, 97); asia.lineTo(293, 81); asia.lineTo(340, 90);
            asia.lineTo(370, 126); asia.lineTo(344, 159); asia.lineTo(298, 136);
            asia.lineTo(273, 147); asia.close();
            c.drawPath(asia, p);
            for (int i = 0; i < 180; i++) {
                float xx = 154 + (i * 41) % 251;
                float yy = 76 + (i * 67) % 149;
                circle(c, i % 6 == 0 ? GLOW : 0xA5DDA34B, xx, yy, i % 13 == 0 ? 1.7f : .8f);
            }
            c.restoreToCount(clipped);
            p.setShader(null);
            p.setStyle(Paint.Style.STROKE);
            p.setColor(GOLD); p.setStrokeWidth(2.6f);
            c.drawCircle(268, 237, 206, p);
            p.setStyle(Paint.Style.FILL);
            p.setShader(new LinearGradient(0, 155, 0, 230,
                    new int[]{0x0006050A, 0xD806050A}, null, Shader.TileMode.CLAMP));
            c.drawRect(0, 154, 400, 230, p); p.setShader(null);
            original.restoreToCount(saved);
        }
    }

    /** A native illustrated gold-on-black tile rather than HTML/WebView content. */
    static final class TileDrawable extends Art {
        private final int kind;
        TileDrawable(int kind) { this.kind = kind; }
        @Override public void draw(Canvas original) {
            android.graphics.Rect bounds = getBounds();
            int saved = original.save();
            original.translate(bounds.left, bounds.top);
            float w = Math.max(1, bounds.width());
            float h = Math.max(1, bounds.height());
            original.scale(w / 240f, h / 155f);
            Canvas c = original;
            p.setColor(Color.WHITE);
            p.setShader(new LinearGradient(10, 0, 230, 155,
                    new int[]{0xFF18263B, 0xFF131018, 0xFF09070C}, null, Shader.TileMode.CLAMP));
            c.drawRoundRect(new RectF(1, 1, 239, 154), 13, 13, p); p.setShader(null);
            for (int i = 0; i < 20; i++)
                circle(c, 0x60F6CB72, (i * 31 + kind * 17) % 238, (i * 23) % 103, .7f);

            switch (kind) {
                case 0: globe(c); break;
                case 1: messages(c); break;
                case 2: coins(c); break;
                case 3: pin(c); break;
                case 4: envelope(c); break;
                case 5: bag(c); break;
                case 6: television(c); break;
                case 7: controller(c); break;
                default: books(c); break;
            }
            p.setShader(new LinearGradient(0, 75, 0, 155,
                    new int[]{0x0006040A, 0xFB06040A}, null, Shader.TileMode.CLAMP));
            c.drawRoundRect(new RectF(2, 70, 238, 153), 12, 12, p); p.setShader(null);
            p.setColor(0xFFF7D07C); p.setStyle(Paint.Style.STROKE); p.setStrokeWidth(2);
            c.drawRoundRect(new RectF(1, 1, 239, 154), 13, 13, p);
            p.setStyle(Paint.Style.FILL);
            original.restoreToCount(saved);
        }
        private void stroke(Canvas c, float width) {
            p.setShader(null); p.setStyle(Paint.Style.STROKE); p.setStrokeWidth(width);
            p.setStrokeCap(Paint.Cap.ROUND); p.setStrokeJoin(Paint.Join.ROUND); p.setColor(GOLD);
        }
        private void globe(Canvas c) {
            p.setShader(null); p.setColor(0xFF09273C); p.setStyle(Paint.Style.FILL);
            c.drawCircle(120, 62, 43, p);
            stroke(c, 3); c.drawCircle(120, 62, 43, p);
            c.drawOval(new RectF(97, 19, 143, 105), p);
            line(c, GOLD, 2, 79, 63, 161, 63);
            p.setColor(0xFFA67B31); p.setStyle(Paint.Style.FILL);
            Path land = new Path(); land.moveTo(89, 34); land.lineTo(117, 26);
            land.lineTo(125, 48); land.lineTo(110, 59); land.lineTo(108, 79);
            land.lineTo(92, 67); land.close(); c.drawPath(land, p);
            stroke(c, 2); c.drawOval(new RectF(47, 46, 195, 86), p);
            p.setStyle(Paint.Style.FILL);
        }
        private void messages(Canvas c) {
            p.setColor(0xFF0F172C); c.drawRoundRect(new RectF(58, 28, 161, 91), 20, 20, p);
            stroke(c, 4); c.drawRoundRect(new RectF(58, 28, 161, 91), 20, 20, p);
            c.drawRoundRect(new RectF(121, 58, 191, 106), 15, 15, p);
            p.setStyle(Paint.Style.FILL);
            for (int i = 0; i < 3; i++) circle(c, GLOW, 83 + i * 27, 58, 4);
        }
        private void coins(Canvas c) {
            for (int i = 0; i < 4; i++) {
                int x = 54 + i * 38, stack = 1 + (i % 3);
                for (int j = 0; j < stack; j++) {
                    p.setColor(0xFF95611D);
                    c.drawRect(x, 95 - j * 13, x + 29, 104 - j * 13, p);
                    oval(c, GOLD, x, 90 - j * 13, x + 29, 101 - j * 13);
                }
            }
            stroke(c, 4); c.drawCircle(122, 50, 32, p); p.setStyle(Paint.Style.FILL);
            p.setTypeface(Typeface.create(Typeface.SERIF, Typeface.BOLD));
            p.setTextSize(38); p.setTextAlign(Paint.Align.CENTER); p.setColor(GLOW);
            c.drawText("S", 122, 63, p);
        }
        private void pin(Canvas c) {
            Path path = new Path();
            path.moveTo(120, 112); path.cubicTo(75, 68, 81, 24, 120, 24);
            path.cubicTo(162, 24, 165, 65, 120, 112); path.close();
            p.setColor(0xFF100D13); c.drawPath(path, p);
            stroke(c, 5); c.drawPath(path, p); p.setStyle(Paint.Style.FILL);
            circle(c, GLOW, 120, 61, 16);
            for (int i = 0; i < 4; i++)
                line(c, 0xFF73562C, 1.7f, 30 + i * 50, 130, 80 + i * 50, 112);
        }
        private void envelope(Canvas c) {
            p.setColor(0xFF0C1C34); c.drawRoundRect(new RectF(54, 37, 187, 105), 7, 7, p);
            stroke(c, 4); c.drawRoundRect(new RectF(54, 37, 187, 105), 7, 7, p);
            line(c, GLOW, 3, 57, 40, 120, 86);
            line(c, GLOW, 3, 120, 86, 184, 40);
            line(c, GOLD, 2, 57, 102, 95, 74);
            line(c, GOLD, 2, 184, 102, 145, 74);
        }
        private void bag(Canvas c) {
            p.setColor(0xFF8A561A); c.drawRoundRect(new RectF(77, 43, 164, 111), 4, 4, p);
            stroke(c, 4); c.drawRoundRect(new RectF(77, 43, 164, 111), 4, 4, p);
            c.drawArc(new RectF(97, 19, 144, 67), 180, 180, false, p); p.setStyle(Paint.Style.FILL);
        }
        private void television(Canvas c) {
            p.setColor(0xFF080B15); c.drawRoundRect(new RectF(71, 43, 169, 111), 6, 6, p);
            stroke(c, 4); c.drawRoundRect(new RectF(71, 43, 169, 111), 6, 6, p);
            line(c, GOLD, 9, 71, 33, 169, 20);
            Path triangle = new Path(); triangle.moveTo(112, 60);
            triangle.lineTo(112, 94); triangle.lineTo(143, 77); triangle.close();
            p.setStyle(Paint.Style.FILL); p.setColor(GOLD); c.drawPath(triangle, p);
        }
        private void controller(Canvas c) {
            Path outline = new Path();
            outline.moveTo(88, 47); outline.cubicTo(65, 48, 60, 70, 55, 102);
            outline.cubicTo(55, 119, 75, 117, 93, 95);
            outline.lineTo(147, 95); outline.cubicTo(170, 118, 187, 117, 186, 100);
            outline.cubicTo(181, 62, 176, 46, 150, 47); outline.close();
            p.setColor(0xFF151924); c.drawPath(outline, p);
            stroke(c, 5); c.drawPath(outline, p); p.setStyle(Paint.Style.FILL);
            line(c, GOLD, 5, 78, 78, 106, 78); line(c, GOLD, 5, 92, 64, 92, 92);
            circle(c, GOLD, 147, 69, 5); circle(c, GLOW, 160, 81, 5);
        }
        private void books(Canvas c) {
            p.setColor(0xFF64421C);
            for (int i = 0; i < 5; i++) c.drawRect(56 + i * 27, 42, 77 + i * 27, 116, p);
            for (int i = 0; i < 5; i++)
                line(c, GOLD, 3, 61 + i * 27, 55, 61 + i * 27, 104);
            circle(c, 0xFFFDE3A7, 121, 36, 23);
            p.setColor(0xFF231A11); c.drawRect(112, 55, 129, 72, p);
        }
    }
}
