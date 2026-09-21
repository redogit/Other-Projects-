package org.rmaos.mingx;
import android.content.Context;import android.graphics.*;import android.view.View;
public final class MiniGXHudView extends View {
 private final MiniGXRenderer renderer;private final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
 public MiniGXHudView(Context c,MiniGXRenderer r){super(c);renderer=r;setWillNotDraw(false);setClickable(false);p.setTypeface(Typeface.MONOSPACE);}
 @Override protected void onDraw(Canvas c){super.onDraw(c);MiniGXGameState g=renderer.game();float d=getResources().getDisplayMetrics().density;p.setColor(Color.argb(220,245,240,230));p.setTextSize(13*d);p.setFakeBoldText(true);c.drawText("RMAOS MiniGX · W114 / 5 OBSERVERS",16*d,28*d,p);p.setTextSize(11*d);p.setColor(Color.rgb(255,210,95));c.drawText(String.format(java.util.Locale.US,"%06d  ×%d",g.score(),g.combo()),16*d,47*d,p);p.setColor(Color.rgb(105,240,255));c.drawText(g.objectId(),16*d,66*d,p);p.setColor(statusColor(g.status()));c.drawText(g.status()+"  "+g.lastTransform()+"  I="+String.format(java.util.Locale.US,"%.2f",g.integrity())+"  T="+g.uniqueTransforms(),16*d,84*d,p);p.setColor(Color.argb(190,190,180,200));p.setTextSize(9*d);p.setFakeBoldText(false);c.drawText("tap ∂ · drag ROTATE · pinch IN/OUT · double-tap REVERSE · hold RECENTER",16*d,getHeight()-22*d,p);postInvalidateOnAnimation();}
 private static int statusColor(String s){if("REJECTED".equals(s))return Color.rgb(145,140,145);if("PARTIAL".equals(s))return Color.rgb(255,170,65);if("ROBUST".equals(s))return Color.rgb(145,255,160);return Color.rgb(220,190,255);}
}
