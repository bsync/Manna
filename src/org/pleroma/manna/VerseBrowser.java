package org.pleroma.manna;

import org.pleroma.manna.R;
import org.bsync.android.*;
import android.app.Activity;
import android.os.Bundle;
import android.content.Context;
import android.content.res.*;
import android.view.*;
import android.widget.*;
import android.util.Log;
import java.io.*;
import java.util.*;
import java.lang.Math;

public class VerseBrowser extends Activity implements Gestured {
   @Override
   public void onCreate(Bundle savedInstanceState) {
      super.onCreate(savedInstanceState);
      setContentView(R.layout.verse_browser);
      verseView = (TextView) findViewById(R.id.verseview);
      vgHandler = new GestureHandler(this);
      String bookName = getIntent().getStringExtra("Book");
      book = CanonBrowser.theCanon.select(bookName);
      int intentedChapter = getIntent().getIntExtra("Chapter", 1);
      chapter = book.select(intentedChapter);
      int intentedVerse = getIntent().getIntExtra("Verse", 1);
      setVerse(intentedVerse);
   }
   private GestureHandler vgHandler;
   private TextView verseView;
   private Book book;
   private Chapter chapter;
   private Verse verse;

   /* For some reason this method has to be overriden to call the 
    * GestureHandler's onTouchEvent method in order for the verseView
    * (TextView) to properly recognize Gesture type motion events.
    *
    * This seems like a bug in one of the android classes somewhere.
    * */
   @Override
   public boolean dispatchTouchEvent(MotionEvent ev) {
      super.dispatchTouchEvent(ev);
      return vgHandler.onTouchEvent(ev);
   }

   private int setVerse(int targetVerse) {
      if(targetVerse > 0 && targetVerse <= chapter.count()) {
         verse=chapter.select(targetVerse);
         verseView.setText(verse.toString());
         setTitle(chapter.number + ":" + verse.number 
                  + " of " + book.whatIsIt());
      }
      return verse.number;
   }

   /*Gestured Interface*/
   public Context context() { return this; }
   public View gesturedView() { return verseView; }
   public boolean onXFling (float velocityX) { return false; }
   public boolean onYFling(float velocityY) {
      Log.i("VB", "detected verse fling");
      int vbump = (int) (velocityY/Math.abs(velocityY));
      setVerse(verse.number - vbump);
      Log.i("VB", "onFling changed to verse: " + verse.number);
      return true;
   }
}
