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
      MannaIntent scriptIntent = getMannaIntent();

      book = CanonBrowser.theCanon.select(scriptIntent.name());
      chapter = book.select(scriptIntent.chapter());
      super.onCreate(savedInstanceState);
      setCurrentItem(scriptIntent.chapter());
   }
   private Book book;
   private Chapter chapter;

   protected int fragCount() { return chapter.count(); }
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
            Verse vs = chapter.select(pos+1);
            startActivity(newMannaIntent(vs, VerseBrowser.class));
         }
      };
   }

   protected void onMannaSelected(int whichManna) { 
      chapter = book.select(whichManna);
      session.push(newMannaIntent(chapter, this.getClass()));
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

