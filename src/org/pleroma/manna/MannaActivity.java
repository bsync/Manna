package org.pleroma.manna;
import android.os.Bundle;
import android.content.Context;
import android.content.Intent;
import android.support.v4.app.*;
import android.support.v4.view.*;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Spinner;
import android.widget.TextView;
import java.util.List;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Collections;
import android.util.Log;

public abstract class MannaActivity extends FragmentActivity {
   protected void onCreate(Bundle savedInstanceState) {
      requestWindowFeature(Window.FEATURE_CUSTOM_TITLE);
      mvp = new ViewPager(this);
      mvp.setId(R.id.pager);
      mvp.setOnPageChangeListener(
         new ViewPager.SimpleOnPageChangeListener() {
            public void onPageSelected (int position) {
               onMannaSelected(position+1);
            }
         });
      mvp.setAdapter(new MannaAdapter(getSupportFragmentManager()));
      setContentView(mvp);
      getWindow().setFeatureInt(Window.FEATURE_CUSTOM_TITLE, R.layout.tbar);
      initSessionSpinner();
      super.onCreate(savedInstanceState);
   }
   private ViewPager mvp;
   protected static LinkedHashMap<String, Intent> session 
      = new LinkedHashMap<String, Intent>();
   private boolean sessionInitInProgress;

   abstract protected String mannaRef();
   abstract protected int mannaCount();
   protected abstract Fragment newFragment();

   private void initSessionSpinner() {
      sessionInitInProgress = true;
      Spinner sessionSpinner = (Spinner) findViewById(R.id.titlebar);
      List<String> sList = new ArrayList<String>(session.keySet());
      Collections.reverse(sList);
      sessionSpinner.setAdapter(
         new ArrayAdapter(this,
            android.R.layout.simple_spinner_item, 
            sList)
         );
      for(int i=0;  i < sList.size(); i++) {
         if(sList.get(i).equals(mannaRef())) {
            sessionSpinner.setSelection(i);
         }
      }
      sessionSpinner.setOnItemSelectedListener(this.sessionHandler);
   }

   protected void setCurrentItem(int position) {
      mvp.setCurrentItem(position-1, true);
   }

   protected void onMannaSelected(int whichManna) { }

   private class MannaAdapter extends FragmentStatePagerAdapter {
      public MannaAdapter(FragmentManager fm) { super(fm); }

      @Override
      public Fragment getItem(int position) { 
         Fragment frag = newFragment();
         Bundle args = new Bundle();
         args.putInt("pos", position+1);
         frag.setArguments(args);
         return frag;
      }

      @Override
      public int getCount() { return mannaCount(); }
   }


   private AdapterView.OnItemSelectedListener sessionHandler = 
         new AdapterView.OnItemSelectedListener() {
            public void onItemSelected(AdapterView<?> parent, View view, 
                                       int position, long id) { 
               if(sessionInitInProgress) { sessionInitInProgress=false; }
               else {
                  String mannaName = 
                     (String) parent.getItemAtPosition(position);
                     startActivity(session.get(mannaName)); 
               }
            }
            public void onNothingSelected(AdapterView<?> parent) { }
         };
}
