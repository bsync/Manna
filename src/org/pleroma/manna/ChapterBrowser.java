package org.pleroma.manna;

import org.pleroma.manna.R;
import android.app.ListActivity;
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

public class ChapterBrowser extends MannaActivity {

   public void onCreate(Bundle savedInstanceState) { 
      super.onCreate(savedInstanceState);
      bookManna = theCanon.select(super.mannaIntent().name());
      page(super.mannaIntent().chapter());
   }
   private Book bookManna;

   protected int getMannaFragCount() { return bookManna.count(); }

   protected Fragment getMannaFragment(int position) { 
      Chapter currentChapter = bookManna.select(position+1);
      ChapterAdapter ca = new ChapterAdapter(currentChapter);
      ListFragment chapterFrag = new ListFragment();
      chapterFrag.setListAdapter(ca);
      return chapterFrag;
   }

   protected MannaIntent mannaIntent() {
      Chapter currentChapter = bookManna.select(page());
      return new MannaIntent(this, currentChapter, ChapterBrowser.class);
   }

   public void onClick(View v) {
      int verseId = v.getId();
      Chapter chapterManna = bookManna.select(page());
      Verse verseManna = chapterManna.select(verseId);
      Log.i("CB", "Launching intent for " + verseManna);
      startActivity(new MannaIntent(this, verseManna, ScriptBrowser.class));
   }

   private class ChapterAdapter extends ArrayAdapter<Verse> {
      public ChapterAdapter(Chapter cmanna) {
         super(ChapterBrowser.this, R.layout.button, cmanna.manna());
      }

      @Override
      public View getView(int position, View convertView, ViewGroup parent) {
         Button buttonView = (Button) convertView;
         if (buttonView == null) {
            LayoutInflater vi = 
               (LayoutInflater)
                  getSystemService(Context.LAYOUT_INFLATER_SERVICE);
            buttonView = (Button) vi.inflate(R.layout.chapter_button, null);
            buttonView.setOnClickListener(ChapterBrowser.this);
         }
         Verse verse = getItem(position);
         buttonView.setText(verse.whatIsIt()); 
         buttonView.setId(verse.number);
         return buttonView;
      }
   }
}
