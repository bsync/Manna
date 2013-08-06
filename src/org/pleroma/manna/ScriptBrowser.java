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
      super.onCreate(savedInstanceState);
      Book book = theCanon.select(super.mannaIntent().name());
      int c = super.mannaIntent().chapter();
      chapterManna = book.select(c);
      int v = super.mannaIntent().verse();
      page(v);
   }
   private Chapter chapterManna;

   protected int getMannaFragCount() { return chapterManna.count(); }
   protected Fragment getMannaFragment(int pos) {
      Fragment verseFrag = new Fragment() {
         public View onCreateView(LayoutInflater inf, 
                                  ViewGroup container,
                                  Bundle savedInstanceState) {
            TextView tv = (TextView) inf.inflate(R.layout.scriptview, null);
            tv.setText(getArguments().getString("vtext"));
            return tv;
         }
      };
      Bundle b = new Bundle();
      b.putString("vtext", chapterManna.select(pos+1).whatIsIt());
      verseFrag.setArguments(b);

      return verseFrag;
   }

   protected MannaIntent mannaIntent() {
      Verse v = chapterManna.select(page());
      MannaIntent sIntent = new MannaIntent(this, v, ScriptBrowser.class);
      return sIntent;
   }

   /*
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
   */
}

