package org.pleroma.manna;

import org.pleroma.manna.BookSet;

import android.app.ListActivity;
import android.content.Context;
import android.content.Intent;
import android.support.v4.app.*;
import android.view.*;
import android.os.Bundle;
import android.widget.*;
import java.util.*;
import java.lang.Math;
import android.util.Log;

public class BookBrowser extends MannaActivity {
   public void onCreate(Bundle savedInstanceState) { 
      super.onCreate(savedInstanceState);
      books = theCanon.books();
      Book currentBook = theCanon.select(super.mannaIntent().name());
      pageIndex(books.indexOf(currentBook));
   }
   private List<Book> books;

   protected int getMannaFragCount() { return books.size(); }

   protected Fragment getMannaFragment(int position) {
      Book book = books.get(position);
      ListFragment bFrag = new ListFragment();
      bFrag.setListAdapter(new BookAdapter(book.count()));
      return bFrag;
   }

   protected MannaIntent mannaIntent() {
      Book currentBook = books.get(pageIndex());
      return new MannaIntent(this, currentBook, BookBrowser.class);
   }

   public void onClick(View v) {
      Book currentBook = books.get(pageIndex());
      int chapterId = v.getId();
      Chapter c = currentBook.select(chapterId);
      startActivity(new MannaIntent(this, c, ChapterBrowser.class));
   }

   private class BookAdapter extends ArrayAdapter<Integer> {

      public BookAdapter(int bookCount) {
         super(BookBrowser.this, R.layout.button);
         for(int i = 1; i <= bookCount; i++) { add(i); }
      }

      @Override
      public View getView(int position, View convertView, ViewGroup parent) {
         Button buttonView = (Button) convertView;
         if (buttonView == null) {
            LayoutInflater vi = 
               (LayoutInflater)
                  getSystemService(Context.LAYOUT_INFLATER_SERVICE);
            buttonView = (Button) vi.inflate(R.layout.button, null);
            int viewHeight=parent.getHeight();
            buttonView.setHeight(viewHeight/Math.min(getCount(), 7));
         }
         Integer chapter = getItem(position);
         buttonView.setId(chapter);
         buttonView.setText(chapter.toString()); 
         buttonView.setOnClickListener(BookBrowser.this);
         return buttonView;
      }
   }
}
