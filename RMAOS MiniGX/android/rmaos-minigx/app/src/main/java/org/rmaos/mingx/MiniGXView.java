package org.rmaos.mingx;
import android.content.Context;import android.opengl.GLSurfaceView;import android.view.*;
public final class MiniGXView extends GLSurfaceView {
 private final MiniGXRenderer renderer;private final GestureDetector gestures;private final ScaleGestureDetector scale;private float lastX,lastY;
 public MiniGXView(Context c){super(c);setEGLContextClientVersion(3);setPreserveEGLContextOnPause(true);renderer=new MiniGXRenderer(c);setRenderer(renderer);setRenderMode(RENDERMODE_CONTINUOUSLY);
  gestures=new GestureDetector(c,new GestureDetector.SimpleOnGestureListener(){@Override public boolean onSingleTapConfirmed(MotionEvent e){renderer.firePulse();performClick();return true;}@Override public boolean onDoubleTap(MotionEvent e){renderer.reverse();return true;}@Override public void onLongPress(MotionEvent e){renderer.homeward();performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);}});
  scale=new ScaleGestureDetector(c,new ScaleGestureDetector.SimpleOnScaleGestureListener(){@Override public boolean onScale(ScaleGestureDetector d){renderer.scale(d.getScaleFactor());return true;}});
 }
 public MiniGXRenderer renderer(){return renderer;} @Override public boolean performClick(){super.performClick();return true;}
 @Override public boolean onTouchEvent(MotionEvent e){scale.onTouchEvent(e);gestures.onTouchEvent(e);switch(e.getActionMasked()){case MotionEvent.ACTION_DOWN:lastX=e.getX();lastY=e.getY();return true;case MotionEvent.ACTION_MOVE:if(!scale.isInProgress()){float dx=e.getX()-lastX,dy=e.getY()-lastY;renderer.rotate(dx*.006f,dy*.006f);lastX=e.getX();lastY=e.getY();}return true;default:return true;}}
}
