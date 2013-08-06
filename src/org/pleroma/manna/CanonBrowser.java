package org.pleroma.manna;

import org.pleroma.manna.R;
import android.app.Activity;
import android.content.res.*;
import android.content.Intent;
import android.os.Bundle;
import android.support.v4.app.Fragment;
import android.view.*;
import android.support.v4.app.*;
import android.widget.*;
import android.util.Log;
import java.io.*;
import java.util.*;

public class CanonBrowser extends MannaActivity {
   @Override
   public void onCreate(Bundle savedInstanceState) {
      super.onCreate(savedInstanceState);
      ot = theCanon.oldTestament();
      nt = theCanon.newTestament();
   }
   private OldTestament ot;
   private NewTestament nt;

   protected int getMannaFragCount() { return 1; }

   protected Fragment getMannaFragment(int position) { 
      ListFragment canonFrag = new ListFragment();
      canonFrag.setListAdapter(new CanonAdapter());
      return canonFrag; 
   }

   protected MannaIntent mannaIntent() { 
      MannaIntent canonIntent 
         = new MannaIntent(this, theCanon, CanonBrowser.class);
      canonIntent.setAction(Intent.ACTION_MAIN);
      return canonIntent; 
   }

   public void onClick(View v) { 
      String setKey = (((Button) v).getText()).toString();
      BookSet bookSet = theCanon.selectSet(setKey);
      if( bookSet.count() > 1) {
         Log.i("CB", "Starting book browser for bookset " + setKey);
         startActivity(new MannaIntent(this, bookSet, SetBrowser.class));
      } else {
         startActivity(new MannaIntent(this, bookSet, BookBrowser.class));
      }
   }

   private class CanonAdapter extends ArrayAdapter<BookSet> {
      CanonAdapter() {
         super(CanonBrowser.this, R.layout.button, theCanon.bookSets()); 
      }

      public View getView(int position, View convertView, ViewGroup parent) {
         BookSet bookSetItem = getItem(position);
         Button bv = (Button) convertView;
         if(bookSetItem == ot) {
            bv = (Button) inflater.inflate(R.layout.ot_button, null);
         } else if(bookSetItem == nt) {
            bv = (Button) inflater.inflate(R.layout.nt_button, null);
         } else {
            bv = (Button) inflater.inflate(R.layout.button, null);
         }
         int viewHeight=parent.getHeight();
         bv.setHeight(viewHeight/Math.min(getCount(), 7));
         bv.setText(bookSetItem.whatIsIt());
         bv.setOnClickListener(CanonBrowser.this);
         return bv;
      }
   }
}
