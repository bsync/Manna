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
      Intent vbIntent = getIntent();
      String bookName = vbIntent.getStringExtra("Book");
      Book book = CanonBrowser.theCanon.select(bookName);
      int intentedChapter = vbIntent.getIntExtra("Chapter", 1);
      chapter = book.select(intentedChapter);
      int intentedVerse = vbIntent.getIntExtra("Verse", 1);
      verse = chapter.select(intentedVerse);
      session.put(verse.toString(), vbIntent); 
      super.onCreate(savedInstanceState);
      setCurrentItem(intentedVerse);
   }
   private Chapter chapter;
   private Verse verse;

   protected String mannaRef() { return verse.toString(); }
   protected int mannaCount() { return 1; }
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
