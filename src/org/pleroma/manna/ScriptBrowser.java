package org.pleroma.manna;

import org.pleroma.manna.R;
import android.os.Bundle;
import android.content.Context;
import android.content.Intent;
import android.R.layout;
import android.support.v4.app.*;
import android.util.Log;
import android.view.*;
import android.widget.*;
import java.util.*;

public class ScriptBrowser extends MannaActivity {
   @Override
   protected void onCreate(Bundle savedInstanceState) {
      Intent sbIntent = getIntent();
      String bookName = sbIntent.getStringExtra("Book");
      book = CanonBrowser.theCanon.select(bookName);
      int initChapNum = sbIntent.getIntExtra("Chapter", 1);
      chapter = book.select(initChapNum);
      session.put(chapter.toString(), sbIntent);
      super.onCreate(savedInstanceState);
      setCurrentItem(initChapNum);
   }
   private Book book;
   private Chapter chapter;

   protected String mannaRef() { return chapter.toString(); }
   protected int mannaCount() { return 1; }
   protected Fragment newFragment() {
      return new ListFragment() {
         @Override
         public void onActivityCreated(Bundle savedInstanceState) {
            super.onActivityCreated(savedInstanceState);
            cNum = getArguments() != null ? getArguments().getInt("pos") : 1;
            setListAdapter(new VerseAdapter(book.select(cNum)));
         }
         private int cNum;

         @Override
         public void onListItemClick(ListView l, View v, int pos, long id) {
            Log.i("SB", "onListItemClick"); 
            Intent verseIntent 
               = new Intent(ScriptBrowser.this, VerseBrowser.class);
            verseIntent.putExtra("Book", book.whatIsIt());
            verseIntent.putExtra("Chapter", cNum);
            verseIntent.putExtra("Verse", pos+1);
            startActivity(verseIntent);
         }
      };
   }

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
            textView.setText(selection.whatIsIt()); 
            textView.setId(selection.number);
         }
         return textView;
      }
   }
}

