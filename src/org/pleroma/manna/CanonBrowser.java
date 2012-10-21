package org.pleroma.manna;

import org.pleroma.manna.R;
import android.app.ListActivity;
import android.content.Intent;
import android.content.Context;
import android.content.res.*;
import android.os.Bundle;
import android.view.*;
import android.widget.*;
import android.util.Log;
import java.io.*;
import java.util.*;

public class CanonBrowser extends ListActivity implements View.OnClickListener {

   public void onCreate(Bundle savedInstanceState) { 
      super.onCreate(savedInstanceState);
      setListAdapter(new TestamentAdapter(tList)); 
      theCanon = new Canon(getResources().getAssets()); 
   }
   protected static Canon theCanon;
   private TestamentAdapter tAdapter;
   private final List<String> tList 
      = Arrays.asList("Old Testament", "New Testament");

   public void onClick(View v) {
      String selection = (((Button) v).getText()).toString();
      Intent bookIntent = new Intent(this, BookBrowser.class);
      bookIntent.putExtra("division", selection);
      CanonBrowser.this.startActivity(bookIntent);
   }

   private class TestamentAdapter extends ArrayAdapter<String> {

      public TestamentAdapter(List<String> selection) {
         super(CanonBrowser.this, R.layout.book_title, selection);
      }

      @Override
      public View getView(int position, View convertView, ViewGroup parent) {
         Button buttonView = (Button) convertView;
         if (buttonView == null) {
            LayoutInflater vi = 
               (LayoutInflater)
                  getSystemService(Context.LAYOUT_INFLATER_SERVICE);
            buttonView = (Button) vi.inflate(R.layout.book_title, null);
         }
         String selection = getItem(position);
         if (selection != null) { 
            buttonView.setText(selection); 
            buttonView.setOnClickListener(CanonBrowser.this);
         }
         return buttonView;
      }
   }
}
