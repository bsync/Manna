package org.pleroma.manna;

import org.pleroma.manna.R;
import android.app.ListActivity;
import android.os.Bundle;
import android.content.Context;
import android.content.res.*;
import android.content.Intent;
import android.view.*;
import android.widget.*;
import android.view.GestureDetector.*;

import android.util.Log;
import java.io.*;
import java.util.*;
import java.lang.Math;

public class ScriptBrowser extends ListActivity {
   @Override
   public void onCreate(Bundle savedInstanceState) {
      super.onCreate(savedInstanceState);
      scriptGestureDetector = new GestureDetector(this, scriptGestureListener);
      String bookName = getIntent().getStringExtra("Book");
      book = CanonBrowser.theCanon.select(bookName);
      int intentedChapter = getIntent().getIntExtra("Chapter", 1);
      if(book != null) setChapter(intentedChapter);
   }
   private Book book;
   private int currentChapter = 1;
   private GestureDetector scriptGestureDetector;
   private GestureDetector.SimpleOnGestureListener scriptGestureListener =
      new GestureDetector.SimpleOnGestureListener() {
         public boolean onFling (MotionEvent e1, MotionEvent e2, float velocityX, float velocityY) {
            Log.i("Manna", "Detected horizontal fling of velocity: " + velocityX);
            int speed = (int) Math.abs(velocityX);
            if(speed > 30){
               int cbump = (int) velocityX/speed;
               setChapter(currentChapter - cbump);
            }
            return true;
         }
      };


   private int setChapter(int targetChapter) {
      if(targetChapter > 0 && targetChapter <= book.count()) {
         currentChapter=targetChapter;
         setListAdapter(new VerseAdapter(book.select(currentChapter)));
         setTitle("Chapter " + currentChapter + " of " + book.whatIsIt());
      }
      return currentChapter;
   }

   private class VerseAdapter extends BaseAdapter {
      public VerseAdapter(Chapter chapter) {
         super();
         verseChapter = chapter;
         verseIntent = new Intent(ScriptBrowser.this, VerseBrowser.class);
      }
      private Chapter verseChapter;
      private Intent verseIntent;

      public long getItemId(int pos) { return pos; }
      public Verse getItem(int pos) { return verseChapter.select(pos+1); }
      public int getCount() { return verseChapter.count(); }

      @Override
      public View getView(int position, View convertView, ViewGroup parent) {
         Button buttonView = (Button) convertView;
         if (buttonView == null) {
            LayoutInflater vi = 
               (LayoutInflater)
                  getSystemService(Context.LAYOUT_INFLATER_SERVICE);
            buttonView = (Button) vi.inflate(R.layout.verse_button, null);
            buttonView.setOnTouchListener(new View.OnTouchListener() {
               public boolean onTouch(View v, MotionEvent e) { 
                  return scriptGestureDetector.onTouchEvent(e); 
               } });
            buttonView.setOnClickListener(new View.OnClickListener() {
               public void onClick(View v) {
                  verseIntent.putExtra("Book", ScriptBrowser.this.book.whatIsIt());
                  verseIntent.putExtra("Chapter", verseChapter.number);
                  verseIntent.putExtra("Verse", v.getId());
                  ScriptBrowser.this.startActivity(verseIntent);
               } });
         }
         Verse selection = getItem(position);
         if (selection != null) { 
            buttonView.setText(selection.number + selection.toString()); 
            buttonView.setId(selection.number);
         }
         return buttonView;
      }
   }
}
