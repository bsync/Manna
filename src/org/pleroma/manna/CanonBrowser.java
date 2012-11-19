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
      theCanon = new Canon(getResources().getAssets()); 
      setListAdapter(
            new DivisionAdapter(
               new ArrayList<Division>(
                  theCanon.divisions.values())));
      setTitle("Select book or division:");
   }
   protected static Canon theCanon;

   public void onClick(View v) {
      String selection = (((Button) v).getText()).toString();
      Division selectedDiv = theCanon.divisions.get(selection);
      if(selectedDiv.books.size() > 1) {
         Intent bookIntent = new Intent(this, BookBrowser.class);
         bookIntent.putExtra("division", selection);
         CanonBrowser.this.startActivity(bookIntent);
      } else {
         Intent chapterIntent = new Intent(this, ChapterBrowser.class);
         chapterIntent.putExtra("Book", selection);
         CanonBrowser.this.startActivity(chapterIntent);
      }
   }

   private class DivisionAdapter extends ArrayAdapter<Division> {
      public DivisionAdapter(List<Division> divs) {
         super(CanonBrowser.this, 0, divs);
         layoutInflater = CanonBrowser.this.getLayoutInflater();
      }
      private LayoutInflater layoutInflater;

      @Override
      public View getView(int position, View convertView, ViewGroup parent) {
         Division selectedDivision = getItem(position);
         Button buttonView = (Button) convertView;
         if (buttonView == null) {
            if(getItemViewType(position) == OLD_TESTAMENT_ITEM_TYPE) {
               buttonView = (Button) layoutInflater.inflate(R.layout.ot_button, null);
            } else if(getItemViewType(position) == NEW_TESTAMENT_ITEM_TYPE) {
               buttonView = (Button) layoutInflater.inflate(R.layout.nt_button, null);
            } else {
               buttonView = (Button) layoutInflater.inflate(R.layout.button, null);
            }
         }
         buttonView.setText(selectedDivision.toString());
         buttonView.setOnClickListener(CanonBrowser.this);
         return buttonView;
      }

      public int getViewTypeCount() { return 3; }
      public int getItemViewType(int position) { 
         Division positionedDivision = getItem(position);
         if(positionedDivision == theCanon.oldTestament) return OLD_TESTAMENT_ITEM_TYPE;
         if(positionedDivision == theCanon.newTestament) return NEW_TESTAMENT_ITEM_TYPE;
         return SUB_TESTAMENT_TYPE;
      }
      final private int OLD_TESTAMENT_ITEM_TYPE = 0;
      final private int NEW_TESTAMENT_ITEM_TYPE = 1;
      final private int SUB_TESTAMENT_TYPE = 2;
   }
}
