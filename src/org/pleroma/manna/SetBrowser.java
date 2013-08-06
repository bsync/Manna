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

public class SetBrowser extends MannaActivity {

   public void onCreate(Bundle savedInstanceState) { 
      super.onCreate(savedInstanceState);
      bookSets=theCanon.bookSets();
      BookSet initialSet = theCanon.selectSet(super.mannaIntent().name());
      pageIndex(bookSets.indexOf(initialSet));
   }
   private List<BookSet> bookSets;

   protected int getMannaFragCount() { return bookSets.size(); }

   protected Fragment getMannaFragment(int position) {
      BookSet fragmentSet = bookSets.get(position);
      ListFragment setFrag = new ListFragment();
      setFrag.setListAdapter(new SetAdapter(fragmentSet));
      return setFrag;
   }
   
   protected MannaIntent mannaIntent() {
      BookSet currentSet = bookSets.get(pageIndex());
      Log.i("SB", "Manna Intent for bookset: " + currentSet);
      return new MannaIntent(this, currentSet, SetBrowser.class);
   }

   public void onClick(View v) {
      BookSet currentSet = bookSets.get(pageIndex());
      String selection = (((Button) v).getText()).toString();
      Book b = currentSet.select(selection);
      startActivity(new MannaIntent(this, b, BookBrowser.class));
   }

   private class SetAdapter extends ArrayAdapter<Book> {
      public SetAdapter(BookSet bookSet) {
         super(SetBrowser.this, R.layout.button, bookSet.books());
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
            buttonView.setOnClickListener(SetBrowser.this);
         }
         return buttonView;
      }
   }
}
