package org.pleroma.manna;

import org.pleroma.manna.R;
import android.app.ListActivity;
import android.content.Intent;
import android.content.Context;
import android.content.res.*;
import android.graphics.Color;
import android.graphics.drawable.*;
import android.os.Bundle;
import android.view.*;
import android.widget.*;
import android.util.Log;
import java.io.*;
import java.util.*;

public class CanonBrowser extends ListActivity implements View.OnClickListener {

   public void onCreate(Bundle savedInstanceState) { 
      super.onCreate(savedInstanceState);
      try {
         theCanon = new Spirit(getResources().getAssets()).inspiredCanon; 
      } catch (Exception e) { 
         throw new RuntimeException(e);
      }
      setListAdapter(new BookSetAdaptor(theCanon.bookSets()));
      setTitle("Select a Bookset:");
   }
   protected static Canon theCanon;

   public void onClick(View v) {
      String setKey = (((Button) v).getText()).toString();
      if(theCanon.selectSet(setKey).count() > 1) {
         Intent bookIntent = new Intent(this, BookBrowser.class);
         bookIntent.putExtra("division", setKey);
         CanonBrowser.this.startActivity(bookIntent);
      } else {
         Intent chapterIntent = new Intent(this, ChapterBrowser.class);
         chapterIntent.putExtra("Book", setKey);
         CanonBrowser.this.startActivity(chapterIntent);
      }
   }

   private class BookSetAdaptor extends ArrayAdapter<BookSet> {
      public BookSetAdaptor(List<BookSet> bookSets) {
         super(CanonBrowser.this, 0, bookSets);
         layoutInflater = CanonBrowser.this.getLayoutInflater();
         ot = theCanon.oldTestament();
         nt = theCanon.newTestament();
      }
      private LayoutInflater layoutInflater;
      private OldTestament ot;
      private NewTestament nt;

      public View getView(int position, View convertView, ViewGroup parent) {
         BookSet bookSetItem = getItem(position);
         Button buttonView = (Button) convertView;
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
         int viewHeight=getListView().getHeight();
         buttonView.setHeight(viewHeight/Math.min(getCount(), 7));
         buttonView.setText(bookSetItem.whatIsIt());
         buttonView.setOnClickListener(CanonBrowser.this);
         return buttonView;
      }
   }
}
