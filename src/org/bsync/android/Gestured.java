package org.bsync.android;
import android.content.Context;
import android.view.*;

public interface Gestured {
   Context context();
   View gesturedView();
   public boolean onXFling(float vx);
   public boolean onYFling(float vy);
}
