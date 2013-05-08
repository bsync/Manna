package org.pleroma.manna;

import org.pleroma.manna.R;
import android.os.Bundle;
import android.content.Context;
import android.content.Intent;
import android.R.layout;
import android.support.v4.app.*;
import android.support.v4.view.*;
import android.util.Log;
import android.view.*;
import android.widget.*;
import java.util.*;

public class ScriptBrowser extends FragmentActivity {
   @Override
   protected void onCreate(Bundle savedInstanceState) {
      super.onCreate(savedInstanceState);
      String bookName = getIntent().getStringExtra("Book");
      book = CanonBrowser.theCanon.select(bookName);
      int initChapNum = getIntent().getIntExtra("Chapter", 1);

      ViewPager svp = new ViewPager(this);
      svp.setId(R.id.pager);
      setContentView(svp);
      svp.setAdapter(new ChapterAdapter(getSupportFragmentManager()));
      svp.setOnPageChangeListener(
         new ViewPager.SimpleOnPageChangeListener() {
            public void onPageSelected (int position) {
               setTitle("Chapter " + (position + 1) 
                      + " of " + book.whatIsIt());
            }
         });
      svp.setCurrentItem(initChapNum-1, true);
   }
   private Book book;

   private class ChapterAdapter extends FragmentStatePagerAdapter {
      public ChapterAdapter(FragmentManager fm) { super(fm); }

      @Override
      public Fragment getItem(int position) { 
         ChapterFragment frag = new ChapterFragment();
         Bundle args = new Bundle();
         args.putInt("num", position+1);
         frag.setArguments(args);
         return frag;
      }

      @Override
      public int getCount() { return book.count(); }
   }

   private class ChapterFragment extends ListFragment {
      @Override
      public void onActivityCreated(Bundle savedInstanceState) {
         super.onActivityCreated(savedInstanceState);
         cNum = getArguments() != null ? getArguments().getInt("num") : 1;
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
            textView.setText(selection.number + selection.toString()); 
            textView.setId(selection.number);
         }
         return textView;
      }
   }
}

