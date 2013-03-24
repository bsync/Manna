package org.pleroma.manna;

import org.pleroma.manna.collections.BookSet;

import android.app.ListActivity;
import android.content.Context;
import android.content.Intent;
import android.view.*;
import android.os.Bundle;
import android.widget.*;
import java.util.*;
import android.util.Log;

public class BookBrowser extends ListActivity implements View.OnClickListener {

   public void onCreate(Bundle savedInstanceState) { 
      super.onCreate(savedInstanceState);
      Canon bookCanon = CanonBrowser.theCanon;
      String divisionName = getIntent().getStringExtra("division");
      BookSet selectedBooks = bookCanon.selectBookSet(divisionName);
      setListAdapter(new BookAdapter(selectedBooks));
      setTitle("Select a book from " + selectedBooks.whatIsIt());
   }

   public void onClick(View v) {
      String selection = (((Button) v).getText()).toString();
      Intent chapterIntent = new Intent(this, ChapterBrowser.class);
      chapterIntent.putExtra("Book", selection);
      BookBrowser.this.startActivity(chapterIntent);
   }

   private class BookAdapter extends ArrayAdapter<Book> {

      public BookAdapter(BookSet bookSet) {
         super(BookBrowser.this, R.layout.button, bookSet.books());
      }

      @Override
      public View getView(int position, View convertView, ViewGroup parent) {
         Button buttonView = (Button) convertView;
         if (buttonView == null) {
            LayoutInflater vi = 
               (LayoutInflater)
                  getSystemService(Context.LAYOUT_INFLATER_SERVICE);
            buttonView = (Button) vi.inflate(R.layout.button, null);
         }
         Book selection = getItem(position);
         if (selection != null) { 
            buttonView.setText(selection.whatIsIt()); 
            buttonView.setOnClickListener(BookBrowser.this);
         }
         return buttonView;
      }
   }
}
