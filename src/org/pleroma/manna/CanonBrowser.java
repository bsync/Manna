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

public class CanonBrowser extends ListActivity 
                          implements View.OnClickListener,
                                     View.OnKeyListener {

   public void onCreate(Bundle savedInstanceState) { 
      super.onCreate(savedInstanceState);
      tAdapter = new TestamentAdapter(tList);
      setListAdapter(tAdapter); 

      theCanon = new Canon(getResources().getAssets()); 
      oldTestamentAdapter = new CanonAdapter(theCanon.oldTestament().values());
      newTestamentAdapter = new CanonAdapter(theCanon.newTestament().values());
      getListView().setOnKeyListener(this);
   }
   public Canon theCanon;
   private TestamentAdapter tAdapter;
   private CanonAdapter oldTestamentAdapter;
   private CanonAdapter newTestamentAdapter;
   private final List<String> tList 
      = Arrays.asList("Old Testament", "New Testament");

   public void onClick(View v) {
      String selection = (((Button) v).getText()).toString();
      if(selection == "Old Testament") {
         setListAdapter(oldTestamentAdapter);
      }
      else if (selection == "New Testament") {
         setListAdapter(newTestamentAdapter);
      } 
      else {
         Intent chapterIntent = new Intent(this, ChapterBrowser.class);
         chapterIntent.putExtra("Book", selection);
         CanonBrowser.this.startActivity(chapterIntent);
      }
   }

   public boolean onKey(View v, int keyCode, KeyEvent event) {
      if(keyCode == KeyEvent.KEYCODE_BACK) {
         if(getListAdapter() != tAdapter) {
            setListAdapter(tAdapter);
            return true;
         }
      }
      return false;
   }

   private class CanonAdapter extends ArrayAdapter<Canon.Manna> {

      public CanonAdapter(Collection<Canon.Manna> selection) {
         super(CanonBrowser.this, R.layout.book_title, new ArrayList(selection));
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
         Canon.Manna selection = getItem(position);
         if (selection != null) { 
            buttonView.setText(selection.whatIsIt()); 
            buttonView.setOnClickListener(CanonBrowser.this);
         }
         return buttonView;
      }
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
