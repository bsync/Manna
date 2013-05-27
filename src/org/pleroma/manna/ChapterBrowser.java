package org.pleroma.manna;

import org.pleroma.manna.R;
import android.app.Activity;
import android.content.Intent;
import android.content.Context;
import android.content.res.*;
import android.os.Bundle;
import android.support.v4.app.*;
import android.view.*;
import android.widget.*;
import android.util.Log;
import java.io.*;
import java.util.*;

public class ChapterBrowser extends MannaActivity 
                            implements View.OnKeyListener{ 

   public void onCreate(Bundle savedInstanceState) { 
      MannaIntent chapterIntent = getMannaIntent();
      bookManna = CanonBrowser.theCanon.select(chapterIntent.name());
      super.onCreate(savedInstanceState);
   }
   private Book bookManna;
   private GridView chapterGrid;

   public boolean onKey(View v, int keyCode, KeyEvent event) {
      if(keyCode != KeyEvent.KEYCODE_SEARCH) return false;
      if(event.getAction() == KeyEvent.ACTION_DOWN) { 
         if(event.isLongPress()) {
            longPress = true;
            Log.i("Manna", "Captured long key event for " + keyCode);
            if(chpButtonsPerRow < 6) { 
               chapterGrid.setNumColumns(++chpButtonsPerRow); 
            }
            KeyEvent.changeAction(event, KeyEvent.ACTION_DOWN);
         }
      }
      else if(event.getAction() == KeyEvent.ACTION_UP) {
         if(longPress == false) {
            if(chpButtonsPerRow > 3) { 
               chapterGrid.setNumColumns(--chpButtonsPerRow); 
            }
            Log.i("Manna", "Captured short key event for " + keyCode);
         }
         longPress = false;
      }
      return true;
   }
   private int chpButtonsPerRow = 4;
   private boolean longPress = false;

   protected int fragCount() { return 1; }
   protected Fragment newFragment() {
      return new Fragment() {
         @Override
         public View onCreateView(LayoutInflater inflater, 
                                  ViewGroup container,
                                  Bundle savedInstanceState) {
            List<Integer> numbers = new ArrayList<Integer>();
            for(int i = 1; i <= bookManna.count(); i++) { numbers.add(i); }
            ChapterAdapter ca = new ChapterAdapter(numbers);
            View v = inflater.inflate(R.layout.chapter_browser, 
                                      container, false);
            chapterGrid = (GridView) v.findViewById(R.id.chapterview);
            chapterGrid.setAdapter(ca);
            chapterGrid.setOnKeyListener(ChapterBrowser.this);
            return v;
         }
      };
   }

   private class ChapterAdapter extends ArrayAdapter<Integer> {
      public ChapterAdapter(List<Integer> nums) {
         super(ChapterBrowser.this, R.layout.button, nums);
      }

      @Override
      public View getView(int position, View convertView, ViewGroup parent) {
         Button buttonView = (Button) convertView;
         if (buttonView == null) {
            LayoutInflater vi = 
               (LayoutInflater)
                  getSystemService(Context.LAYOUT_INFLATER_SERVICE);
            buttonView = (Button) vi.inflate(R.layout.button, null);
         }
         Integer chapter = getItem(position);
         buttonView.setId(chapter);
         buttonView.setText(chapter.toString()); 
         buttonView.setOnClickListener(
            new View.OnClickListener() {
               public void onClick(View v) {
                  int chapterId = v.getId();
                  Chapter chapterManna = bookManna.select(chapterId);
                  ChapterBrowser.this.startActivity(
                     newMannaIntent(chapterManna, ScriptBrowser.class));
               }
            }
         );
         return buttonView;
      }
   }
}
