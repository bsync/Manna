package org.pleroma.manna;

import android.content.Context;
import android.util.AttributeSet;
import android.widget.TextView;
import android.widget.Scroller;
import android.graphics.Canvas;
import android.text.method.ScrollingMovementMethod;

public class ScriptView extends TextView {

    public ScriptView(Context context) {
        super(context);
        init(context);
    }

    public ScriptView(Context context, AttributeSet attrs, int defStyle) {
        super(context, attrs, defStyle);
        init(context);
    }

    public ScriptView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init(context);
    }

    private void init(Context context) {
        setMovementMethod(new ScrollingMovementMethod());
        scriptScroller = new Scroller(context);
    }
    public Scroller getScroller() { return scriptScroller; }
    private Scroller scriptScroller;


    public void fling(int vY, int maxY) {
      scriptScroller.fling(getScrollX(), getScrollY(), 0, vY, 0, 0, 0, maxY);
    }

   @Override
   protected void onDraw(Canvas canvas) {
       // ....your drawings....

       // scrollTo invalidates, so until animation won't finish it will be called
       // (used after a Scroller.fling() )
       super.onDraw(canvas);
       if(scriptScroller.computeScrollOffset()) {
           scrollTo(scriptScroller.getCurrX(), scriptScroller.getCurrY());
       }
   }
}

