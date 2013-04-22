package org.bsync.android;

import android.content.res.*;
import android.view.*;
import android.view.GestureDetector.*;
import android.util.Log;
import java.lang.Math;

public class GestureHandler {

   public GestureHandler(Gestured gc) {
      gClient = gc;
      agDetector = new GestureDetector(gClient.context(), agListener);
      asgDetector = new ScaleGestureDetector(gClient.context(), asgListener);
      View gView = gClient.gesturedView();
      Log.i("GH", "Setting onTouchListener for gView : " + gView);
      gView.setOnTouchListener(new View.OnTouchListener() {
         public boolean onTouch(View v, MotionEvent e) { 
            Log.i("GH", "Sending TouchEvent " + e);
            agDetector.onTouchEvent(e); 
            asgDetector.onTouchEvent(e);
            return false;
         }
      });
   }
   private Gestured gClient;
   private ScaleGestureDetector asgDetector;
   private GestureDetector agDetector;

   /*Technically shouldn't need this but apparently Activities can fail 
    * to pass MotionEvents on to some of thier views (like TextViews)
    * unless they have thier 'dispatchTouchEvent' methods overriden to
    * call this method. */
   public boolean onTouchEvent(MotionEvent ev) {
      return agDetector.onTouchEvent(ev) && asgDetector.onTouchEvent(ev);
   }

   private ScaleGestureDetector.SimpleOnScaleGestureListener asgListener =
      new ScaleGestureDetector.SimpleOnScaleGestureListener() {
         public boolean onScaleBegin (ScaleGestureDetector detector) {
            Log.i("GH", "onScaleBegin event: " + detector);
            return true;
         }
         public boolean onScale (ScaleGestureDetector detector) {
            float scaleFactor = detector.getScaleFactor();
            Log.i("GH", "onScale factor: " + scaleFactor);
            return true;
         }
      };

   private GestureDetector.SimpleOnGestureListener agListener =
      new GestureDetector.SimpleOnGestureListener() {
         public boolean onFling (MotionEvent e1, MotionEvent e2, 
                                 float velocityX, float velocityY) {
            Log.i("GH", "Detected fling: " + velocityX + "," + velocityY);
            int speed = (int) Math.abs(velocityX);
            if(speed > 1000) return gClient.onXFling(velocityX);
            speed = (int) Math.abs(velocityY);
            if(speed > 1000) return gClient.onYFling(velocityY);
            return false;
         }
      };
}
