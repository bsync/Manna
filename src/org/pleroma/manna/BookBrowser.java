package org.pleroma.manna;

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
      DivisionAdapter divisionAdapter = null;
      Log.i("Manna", "Creating BookBrowser for " + divisionName);
      if(divisionName.equals("Old Testament")) {
         divisionAdapter = new DivisionAdapter(bookCanon.oldTestament.books);
         Log.i("Manna", "BookBrowser using " + divisionName);
      }
      else if(divisionName.equals("New Testament")) {
         divisionAdapter = new DivisionAdapter(bookCanon.newTestament.books);
         Log.i("Manna", "BookBrowser using " + divisionName);
      }
      setListAdapter(divisionAdapter); 
   }

   public void onClick(View v) {
      String selection = (((Button) v).getText()).toString();
      Intent chapterIntent = new Intent(this, ChapterBrowser.class);
      chapterIntent.putExtra("Book", selection);
      BookBrowser.this.startActivity(chapterIntent);
   }

   private class DivisionAdapter extends ArrayAdapter<Canon.Manna> {

      public DivisionAdapter(Collection<Canon.Manna> books) {
         super(BookBrowser.this, R.layout.book_title, new ArrayList(books));
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
            buttonView.setText(selection.whatIsIt); 
            buttonView.setOnClickListener(BookBrowser.this);
         }
         return buttonView;
      }
   }
}
