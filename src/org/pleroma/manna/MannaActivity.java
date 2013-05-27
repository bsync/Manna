package org.pleroma.manna;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.support.v4.app.*;
import android.support.v4.view.*;
import android.util.Log;
import android.view.View;
import android.view.Window;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Spinner;
import java.util.ArrayList;
import java.util.regex.*;

public abstract class MannaActivity extends FragmentActivity {
   private static ArrayList<MannaIntent> sessionList 
            = new ArrayList<MannaIntent>();

   protected void onCreate(Bundle savedInstanceState) {
      super.onCreate(savedInstanceState);
      mvp = new ViewPager(this);
      mvp.setId(R.id.pager);
      mvp.setOnPageChangeListener(
         new ViewPager.SimpleOnPageChangeListener() {
            public void onPageSelected (int position) {
               onMannaSelected(position+1);
            }
         });
      mvp.setAdapter(new MannaAdapter(getSupportFragmentManager()));
      requestWindowFeature(Window.FEATURE_CUSTOM_TITLE);
      setContentView(mvp);
      getWindow().setFeatureInt(Window.FEATURE_CUSTOM_TITLE, R.layout.tbar);
      sessionSpinner = (Spinner) findViewById(R.id.session_spinner);
      session = new SessionAdapter(sessionList);
      sessionSpinner.setAdapter(session);
      session.push(getMannaIntent());
      sessionSpinner.setOnItemSelectedListener(this.sessionHandler);
   }
   protected SessionAdapter session;
   private ViewPager mvp;
   private boolean sessionInitInProgress = true;
   private Spinner sessionSpinner;

   protected abstract Fragment newFragment();
   protected abstract int fragCount();

   protected class SessionAdapter extends ArrayAdapter<MannaIntent> {
      SessionAdapter(ArrayList<MannaIntent> s) {
         super(MannaActivity.this, android.R.layout.simple_spinner_item, s);
      }

      public void push(MannaIntent i) {
         sessionList.remove(i);
         sessionList.add(0,i);
         notifyDataSetChanged();
      }
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
      public int getCount() { return fragCount(); }
   }


   private AdapterView.OnItemSelectedListener sessionHandler = 
         new AdapterView.OnItemSelectedListener() {
            public void onItemSelected(AdapterView<?> parent, View view, 
                                       int position, long id) { 
               if(sessionInitInProgress) { sessionInitInProgress=false; }
               else { startActivity(sessionList.get(position)); }
            }
            public void onNothingSelected(AdapterView<?> parent) { }
         };

   public MannaIntent getMannaIntent() { 
      return new MannaIntent(super.getIntent());
   }
   public MannaIntent newMannaIntent(Manna m, Class<?> cls) { 
      return new MannaIntent(m, this, cls);
   }
   protected class MannaIntent extends Intent {
      MannaIntent(Intent i) { 
         super(i); 
         if(getStringExtra("MannaXref") == null) 
            throw new RuntimeException(
                  "Bad motivation: Intent missing MannaXref!"); 
      }

      MannaIntent(Manna m, Intent i) {
         super(i);
         putExtra("MannaXref", m.toString());
      }

      MannaIntent(Manna m, Context packageContext, Class<?> cls) {
         super(packageContext, cls);
         putExtra("MannaXref", m.toString());
      }

      public String name() {
         String mannaXref = toString();
         try {
            mannaXref = mannaXref.split("\\b")[1];
         }
         catch(ArrayIndexOutOfBoundsException aioobe) {
            Log.e("MannaXref", "Failed to split manna: " + mannaXref);
         }
         return mannaXref;
      }

      public int chapter() { 
         Matcher m = Pattern.compile(".*\\s+(\\d+)").matcher(toString());
         m.find();
         return Integer.parseInt(m.group(1)); 
      }

      public int verse() { 
         Matcher m = Pattern.compile(".*\\d+:(\\d+)").matcher(toString());
         m.find();
         return Integer.parseInt(m.group(1)); 
      }

      public String toString() { return getStringExtra("MannaXref"); }

      public boolean equals(Object m) {
         return m.toString().equals(this.toString());
      }

      public int hashCode() { return toString().hashCode(); }
   }
}
