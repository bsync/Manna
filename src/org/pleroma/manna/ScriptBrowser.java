package org.pleroma.manna;

import org.pleroma.manna.R;
import org.bsync.android.*;
import android.app.ListActivity;
import android.os.Bundle;
import android.content.Context;
import android.content.res.*;
import android.content.Intent;
import android.view.*;
import android.widget.*;
import android.R.layout;

import android.util.Log;
import java.io.*;
import java.util.*;
import java.lang.Math;

public class ScriptBrowser extends ListActivity implements Gestured {
   @Override
   public void onCreate(Bundle savedInstanceState) {
      super.onCreate(savedInstanceState);
      sgHandler = new GestureHandler(this);
      String bookName = getIntent().getStringExtra("Book");
      book = CanonBrowser.theCanon.select(bookName);
      int intentedChapter = getIntent().getIntExtra("Chapter", 1);
      if(book != null) setChapter(intentedChapter);
   }
   private GestureHandler sgHandler;
   private Book book;
   private int cnum = 1;

   private int setChapter(int targetChapter) {
      if(targetChapter > 0 && targetChapter <= book.count()) {
         cnum=targetChapter;
         setListAdapter(new VerseAdapter(book.select(cnum)));
         setTitle("Chapter " + cnum + " of " + book.whatIsIt());
      }
      return cnum;
   }

   protected void onListItemClick (ListView l, View v, int pos, long id) {
      Intent verseIntent = new Intent(this, VerseBrowser.class);
      verseIntent.putExtra("Book", book.whatIsIt());
      verseIntent.putExtra("Chapter", cnum);
      verseIntent.putExtra("Verse", pos+1);
      startActivity(verseIntent);
   }

   /*Gestured Interface*/
   public Context context() { return this; }
   public View gesturedView() { return getListView(); }
   public boolean onXFling (float velocityX) {
      Log.i("SB", "Detected Script fling: " + velocityX);
      int cbump = (int) (velocityX/Math.abs(velocityX));
      setChapter(cnum - cbump);
      Log.i("SB", "onFling changed to chapter: " + cnum);
      return true;
   }
   public boolean onYFling (float velocityY) { return false; }

   private class VerseAdapter extends ArrayAdapter<Verse> {
      public VerseAdapter(Chapter chapter) { 
         super(ScriptBrowser.this, 0, chapter.manna());
      }
      @Override
      public View getView(int position, View convertView, ViewGroup parent) {
         TextView textView = (TextView) convertView;
         if (textView == null) {
            LayoutInflater vi = 
               (LayoutInflater)
                  getSystemService(Context.LAYOUT_INFLATER_SERVICE);
            textView = (TextView) vi.inflate(R.layout.verse_button, null);
         }
         Verse selection = getItem(position);
         if (selection != null) { 
            textView.setText(selection.number + selection.toString()); 
            textView.setId(selection.number);
         }
         return textView;
      }
   }
}
