package org.pleroma.manna;
import android.os.Bundle;
import android.content.Intent;
import com.actionbarsherlock.app.*;
import com.actionbarsherlock.view.MenuInflater;
import com.actionbarsherlock.view.Menu;
import android.widget.ArrayAdapter;
import java.util.ArrayList;
import java.util.List;

public class MannaActivity extends SherlockFragmentActivity 
                           implements ActionBar.OnNavigationListener {
   private static List<MannaIntent> sessionHistory = new ArrayList();
   static int sSpinLayout = android.R.layout.simple_spinner_dropdown_item;

   @Override
   protected void onCreate(Bundle savedInstanceState) {
      super.onCreate(savedInstanceState);
      mannaBar = getSupportActionBar();
      mannaBar.setNavigationMode(ActionBar.NAVIGATION_MODE_LIST);
      mannaAdapter = new ArrayAdapter(this, sSpinLayout, sessionHistory);
      mannaBar.setListNavigationCallbacks(mannaAdapter, this);
      mannaBar.setDisplayShowTitleEnabled(false);
      showManna(new MannaIntent(getIntent()));
   }
   ActionBar mannaBar;
   ArrayAdapter<MannaIntent> mannaAdapter;

   public void showManna(MannaIntent shewBread) {
      int layoutId = shewBread.getIntExtra("layout", R.layout.manna_browser);
      setContentView(layoutId);
   }

   public boolean onNavigationItemSelected(int itemPosition, long itemId) {
      return false;  //for now
   }

   public List<MannaIntent> memorize(MannaIntent breadCrumb) {
      sessionHistory.add(breadCrumb);
      mannaAdapter.notifyDataSetChanged();
      return sessionHistory;
   }

   /*
   @Override
   public boolean onCreateOptionsMenu(Menu menu) {
      MenuInflater inflater = getSupportMenuInflater();
      inflater.inflate(R.menu.manna_menu, menu);
      return true;
   }
   */
}

