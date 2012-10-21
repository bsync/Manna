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

      Canon.Manna book = CanonBrowser.theCanon.get(bookName);
      String mannaText = book.chapter(cnum).toString();
      mannaView.setText(mannaText);
      setTitle(bookName + " Chapter " + cnum);
   }
   private TextView mannaView;
}
