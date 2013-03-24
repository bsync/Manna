package org.pleroma.manna;

import org.pleroma.manna.R;
import android.app.Activity;
import android.content.Intent;
import android.content.Context;
import android.content.res.*;
import android.os.Bundle;
import android.view.*;
import android.widget.*;
import android.util.Log;
import java.io.*;
import java.util.*;

public class ChapterBrowser extends Activity implements View.OnKeyListener{ 

   public void onCreate(Bundle savedInstanceState) { 
      super.onCreate(savedInstanceState);
      Log.i("Manna", "Creating ChapterBrowser.");
      bookName = getIntent().getStringExtra("Book");

      setContentView(R.layout.chapter_browser);
      chapterGrid = (GridView) findViewById(R.id.chapterview);
      Book cManna = CanonBrowser.theCanon.lookUp(bookName);
      ArrayList<Integer> chapterNumbers = new ArrayList();
      for(int i = 1; i <= cManna.count(); i++) { chapterNumbers.add(i); }
      chapterGrid.setAdapter(new ChapterAdapter(chapterNumbers));
      setTitle("Select " + bookName + " chapter:");

      chapterGrid.setOnKeyListener(this);
   }
   private String bookName;
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

   private class ChapterAdapter extends ArrayAdapter<Integer> {

      public ChapterAdapter(List<Integer> chptNumbers) {
         super(ChapterBrowser.this, R.layout.button, chptNumbers);
         scriptIntent = new Intent(ChapterBrowser.this, ScriptBrowser.class);
      }
      private Intent scriptIntent;

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
         if (chapter != null) { 
            buttonView.setText(chapter.toString()); 
            buttonView.setOnClickListener(
               new View.OnClickListener() {
                  public void onClick(View v) {
                     scriptIntent.putExtra(
                        "Book", 
                        ChapterBrowser.this.bookName);
                     scriptIntent.putExtra(
                        "Chapter", 
                        Integer.parseInt(((Button) v).getText().toString()));
                     ChapterBrowser.this.startActivity(scriptIntent);
                  }
               }
            );
         }
         return buttonView;
      }
   }
}
