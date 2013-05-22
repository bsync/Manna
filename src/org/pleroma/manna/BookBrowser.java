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

public class BookBrowser extends MannaActivity 
                         implements View.OnClickListener {

   public void onCreate(Bundle savedInstanceState) { 
      Canon bookCanon = CanonBrowser.theCanon;
      Intent bbIntent = getIntent();
      String divisionName = bbIntent.getStringExtra("division");
      selectedSet = bookCanon.selectSet(divisionName);
      session.put(selectedSet.toString(), bbIntent);
      super.onCreate(savedInstanceState);
   }
   private BookSet selectedSet;

   public void onClick(View v) {
      String selection = (((Button) v).getText()).toString();
      Intent chapterIntent = new Intent(this, ChapterBrowser.class);
      chapterIntent.putExtra("Book", selection);
      BookBrowser.this.startActivity(chapterIntent);
   }

   protected String mannaRef() { return selectedSet.toString(); }
   protected int mannaCount() { return selectedSet.count(); }
   protected Fragment newFragment() {
      return new ListFragment() {
         @Override
         public void onActivityCreated(Bundle savedInstanceState) {
            super.onActivityCreated(savedInstanceState);
            setListAdapter(new BookAdapter(selectedSet.books()));
         }

      };
   }

   private class BookAdapter extends ArrayAdapter<Book> {

      public BookAdapter(List<Book> bookSet) {
         super(BookBrowser.this, R.layout.button, bookSet);
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
         Book selection = getItem(position);
         if (selection != null) { 
            buttonView.setText(selection.whatIsIt()); 
            buttonView.setOnClickListener(BookBrowser.this);
         }
         return buttonView;
      }
   }
}
