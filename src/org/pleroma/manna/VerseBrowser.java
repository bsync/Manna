package org.pleroma.manna;
import org.pleroma.manna.R;
import android.app.Activity;
import android.os.Bundle;
import android.content.Context;
import android.content.Intent;
import android.content.res.*;
import android.support.v4.app.*;
import android.support.v4.view.*;
import android.view.*;
import android.widget.*;
import android.util.Log;

public class VerseBrowser extends MannaActivity {

   public void onCreate(Bundle savedInstanceState) {
      MannaIntent verseIntent = getMannaIntent();
      Book book = CanonBrowser.theCanon.select(verseIntent.name());
      chapter = book.select(verseIntent.chapter());
      super.onCreate(savedInstanceState);
      int verseNumber = verseIntent.verse();
      Verse verse = chapter.select(verseNumber);
      setCurrentItem(verseNumber);
   }
   private Chapter chapter;

   protected void onMannaSelected(int whichManna) { 
      Verse verse = chapter.select(whichManna);
      session.push(newMannaIntent(verse, this.getClass()));
   }

   protected int fragCount() { return chapter.count(); }
   protected Fragment newFragment() {
      return new Fragment() {
         @Override
         public View onCreateView(LayoutInflater inflater, 
                                  ViewGroup container,
                                  Bundle savedInstanceState) {
            View v = inflater.inflate(R.layout.verse_browser, 
                                      container, false);
            TextView tv = (TextView) v.findViewById(R.id.verseview);
            int vNum = getArguments() != null 
                                       ? getArguments().getInt("pos") 
                                       : 1;
            Log.i("VB", "Selecting text for verse " + vNum); 
            tv.setText(chapter.select(vNum).whatIsIt());
            return v;
         }
      };
   }
}
