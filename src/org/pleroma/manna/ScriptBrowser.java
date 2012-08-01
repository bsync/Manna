package org.pleroma.manna;

import org.pleroma.manna.R;
import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import android.content.res.*;
import android.util.Log;
import android.text.method.ScrollingMovementMethod;
import java.io.*;
import java.util.*;

public class ScriptBrowser extends Activity 
{
   @Override
   public void onCreate(Bundle savedInstanceState) {
      super.onCreate(savedInstanceState);
      setContentView(R.layout.scripture_view);
      mannaView = (TextView) findViewById(R.id.scripture_view);
      mannaView.setMovementMethod(new ScrollingMovementMethod());
      String bookName = getIntent().getStringExtra("Book");
      int cnum = getIntent().getIntExtra("Chapter", 1);

      Canon theCanon = new Canon(getResources().getAssets());
      Canon.Manna book = theCanon.selectManna(bookName);
      try {
         String mannaText = book.chapter(cnum).toString();
         mannaView.setText(mannaText);
         setTitle(bookName + " Chapter " + cnum);
      }
      catch(IOException ioe) { 
         mannaView.setText("Missing " + bookName + " chapter " + cnum);
         setTitle("ERROR!");
      }
   }
   private TextView mannaView;
}
