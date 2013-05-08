package org.pleroma.manna;
import org.pleroma.manna.R;
import android.app.Activity;
import android.os.Bundle;
import android.content.Context;
import android.content.res.*;
import android.support.v4.app.*;
import android.support.v4.view.*;
import android.view.*;
import android.widget.*;
import android.util.Log;

public class VerseBrowser extends FragmentActivity {

   public void onCreate(Bundle savedInstanceState) {
      super.onCreate(savedInstanceState);
      String bookName = getIntent().getStringExtra("Book");
      book = CanonBrowser.theCanon.select(bookName);
      int intentedChapter = getIntent().getIntExtra("Chapter", 1);
      chapter = book.select(intentedChapter);
      int intentedVerse = getIntent().getIntExtra("Verse", 1);

      ViewPager svp = new ViewPager(this);
      svp.setId(R.id.pager);
      setContentView(svp);
      svp.setAdapter(new VerseAdapter(getSupportFragmentManager()));
      svp.setOnPageChangeListener(
         new ViewPager.SimpleOnPageChangeListener() {
            public void onPageSelected (int position) {
               setTitle("Verse " + (position + 1) 
                      + ", Chapter " + chapter.number
                      + " of " + book.whatIsIt());
            }
         });
      svp.setCurrentItem(intentedVerse-1, true);
   }
   private Book book;
   private Chapter chapter;

   private class VerseAdapter extends FragmentStatePagerAdapter {
      public VerseAdapter(FragmentManager fm) { super(fm); }

      @Override
      public Fragment getItem(int position) { 
         VerseFragment frag = new VerseFragment();
         Bundle args = new Bundle();
         args.putInt("num", position+1);
         frag.setArguments(args);
         return frag;
      }

      @Override
      public int getCount() { return chapter.count(); }
   }

   private class VerseFragment extends Fragment {
      @Override
      public View onCreateView(LayoutInflater inflater, 
                               ViewGroup container,
                               Bundle savedInstanceState) {
         View v = inflater.inflate(R.layout.verse_browser, container, false);
         TextView tv = (TextView) v.findViewById(R.id.verseview);
         int vNum = getArguments() != null ? getArguments().getInt("num") : 1;
         Log.i("VB", "Selecting text for verse " + vNum); 
         ((TextView)tv).setText(chapter.select(vNum).whatIsIt());
         return v;
      }
   }
}
