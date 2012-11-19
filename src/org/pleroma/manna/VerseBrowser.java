package org.pleroma.manna;

import org.pleroma.manna.R;
import android.app.Activity;
import android.os.Bundle;
import android.content.Context;
import android.content.res.*;
import android.view.*;
import android.widget.*;
import android.view.GestureDetector.*;

import android.util.Log;
import java.io.*;
import java.util.*;
import java.lang.Math;

public class VerseBrowser extends Activity {
   @Override
   public void onCreate(Bundle savedInstanceState) {
      super.onCreate(savedInstanceState);
      String bookName = getIntent().getStringExtra("Book");
      book = CanonBrowser.theCanon.get(bookName);
      int intentedChapter = getIntent().getIntExtra("Chapter", 1);
      chapter = book.chapter(intentedChapter);
      int intentedVerse = getIntent().getIntExtra("Verse", 1);
      currentVerse = chapter.verse(intentedVerse);
      verseGestureDetector = new GestureDetector(this, verseGestureListener);
      setContentView(R.layout.verse_browser);
      verseView = (TextView) findViewById(R.id.verseview);
      verseView.setOnTouchListener(new View.OnTouchListener() {
         public boolean onTouch(View v, MotionEvent e) { 
            Log.i("Manna", "onTouch event: " + e);
            verseGestureDetector.onTouchEvent(e); 
            return true;
         }
      });
      setVerse(currentVerse.number);
   }
   private TextView verseView;
   private Canon.Manna book;
   private Chapter chapter;
   private Verse currentVerse;
   private GestureDetector verseGestureDetector;
   private GestureDetector.SimpleOnGestureListener verseGestureListener =
      new GestureDetector.SimpleOnGestureListener() {
         public boolean onFling (MotionEvent e1, MotionEvent e2, float velocityX, float velocityY) {
            Log.i("Manna", "Detected horizontal fling of velocity: " + velocityX);
            int speed = (int) Math.abs(velocityX);
            if(speed > 50){
               int cbump = (int) velocityX/speed;
               if(setVerse(currentVerse.number - cbump) != currentVerse.number) { 
                  Log.i("Manna", "Fling changed to chapter: " + currentVerse.number);
               } else Log.i("Manna", "book chapter count: " + book.chapterCount() + " number: " + currentVerse.number);
            }
            return true;
         }
      };

   private int setVerse(int targetVerse) {
      if(targetVerse > 0 && targetVerse < chapter.verseCount()) {
         currentVerse=chapter.verse(targetVerse);
         verseView.setText(currentVerse.toString());
         setTitle(chapter.number + ":" + currentVerse.number + " of " + book.whatIsIt);
      }
      return currentVerse.number;
   }
}
