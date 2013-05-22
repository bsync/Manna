package org.pleroma.manna;

import org.pleroma.manna.R;
import android.app.ListActivity;
import android.content.Intent;
import android.content.Context;
import android.content.res.*;
import android.graphics.Color;
import android.graphics.drawable.*;
import android.os.Bundle;
import android.support.v4.app.*;
import android.view.*;
import android.widget.*;
import android.util.Log;
import java.io.*;
import java.util.*;

public class CanonBrowser extends MannaActivity 
                          implements View.OnClickListener {

   public void onCreate(Bundle savedInstanceState) { 
      theCanon = new Canon(getResources().getAssets());
      session.put(theCanon.toString(), getIntent());
      ot = theCanon.oldTestament();
      nt = theCanon.newTestament();
      super.onCreate(savedInstanceState);
   }
   protected static Canon theCanon;
   private OldTestament ot;
   private NewTestament nt;

   protected String mannaRef() { return theCanon.toString(); }
   protected int mannaCount() { return 1; }
   protected Fragment newFragment() {
      return new ListFragment() {
         @Override
         public void onActivityCreated(Bundle savedInstanceState) {
            super.onActivityCreated(savedInstanceState);
            setListAdapter(new BookSetAdaptor(theCanon.bookSets()));
         }

      };
   }

   @Override
   public void onClick(View v) {
      Log.i("SB", "onListItemClick"); 
      String setKey = (((Button) v).getText()).toString();
      if(theCanon.selectSet(setKey).count() > 1) {
         Intent bookIntent 
            = new Intent(CanonBrowser.this, BookBrowser.class);
         bookIntent.putExtra("division", setKey);
         CanonBrowser.this.startActivity(bookIntent);
      } else {
         Intent chapterIntent 
            = new Intent(CanonBrowser.this, ChapterBrowser.class);
         chapterIntent.putExtra("Book", setKey);
         CanonBrowser.this.startActivity(chapterIntent);
      }
   }

   private class BookSetAdaptor extends ArrayAdapter<BookSet> {
      public BookSetAdaptor(List<BookSet> bookSets) {
         super(CanonBrowser.this, 0, bookSets);
      }

      public View getView(int position, View convertView, ViewGroup parent) {
         BookSet bookSetItem = getItem(position);
         Button buttonView = (Button) convertView;
         LayoutInflater layoutInflater 
           = CanonBrowser.this.getLayoutInflater();
         if(bookSetItem == ot) {
            buttonView = 
               (Button) layoutInflater.inflate(R.layout.ot_button, null);
         } else if(bookSetItem == nt) {
            buttonView = 
               (Button) layoutInflater.inflate(R.layout.nt_button, null);
         } else {
            buttonView = 
               (Button) layoutInflater.inflate(R.layout.button, null);
         }
         int viewHeight=parent.getHeight();
         buttonView.setHeight(viewHeight/Math.min(getCount(), 7));
         buttonView.setText(bookSetItem.whatIsIt());
         buttonView.setOnClickListener(CanonBrowser.this);
         return buttonView;
      }
   }
}
