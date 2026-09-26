package org.rmaos.mingx;
import android.app.Activity;import android.os.Bundle;import android.view.*;import android.widget.FrameLayout;
public final class MainActivity extends Activity {
 private MiniGXView view;
 @Override protected void onCreate(Bundle b){super.onCreate(b);requestWindowFeature(Window.FEATURE_NO_TITLE);getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);hide();view=new MiniGXView(this);FrameLayout root=new FrameLayout(this);root.addView(view,new FrameLayout.LayoutParams(-1,-1));root.addView(new MiniGXHudView(this,view.renderer()),new FrameLayout.LayoutParams(-1,-1));setContentView(root);}
 private void hide(){if(android.os.Build.VERSION.SDK_INT>=30){WindowInsetsController c=getWindow().getInsetsController();if(c!=null){c.hide(WindowInsets.Type.statusBars()|WindowInsets.Type.navigationBars());c.setSystemBarsBehavior(WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);}}else getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN|View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);}
 @Override protected void onResume(){super.onResume();hide();if(view!=null)view.onResume();}
 @Override protected void onPause(){if(view!=null)view.onPause();super.onPause();}
}
