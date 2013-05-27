package org.pleroma.manna;

import org.pleroma.manna.R;
import android.app.ListActivity;
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
      ot = theCanon.oldTestament();
      nt = theCanon.newTestament();
      super.onCreate(savedInstanceState);
   }
   protected static Canon theCanon;
   private OldTestament ot;
   private NewTestament nt;

   public MannaActivity.MannaIntent getMannaIntent() { 
      return new MannaActivity.MannaIntent(theCanon, super.getIntent());
   }
   protected Fragment newFragment() {
      return new ListFragment() {
         @Override
         public void onActivityCreated(Bundle savedInstanceState) {
            super.onActivityCreated(savedInstanceState);
            setListAdapter(new BookSetAdaptor(theCanon.bookSets()));
         }

      };
   }

   protected int fragCount() { return 1; }

   @Override
   public void onClick(View v) {
      String setKey = (((Button) v).getText()).toString();
      BookSet bookSet = theCanon.selectSet(setKey);
      if( bookSet.count() > 1) {
         CanonBrowser.this.startActivity(
            newMannaIntent(bookSet, BookBrowser.class));
      } else {
         CanonBrowser.this.startActivity(
            newMannaIntent(bookSet, ChapterBrowser.class));
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
