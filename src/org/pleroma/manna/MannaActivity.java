package org.pleroma.manna;
import android.os.Bundle;
import android.support.v4.view.ViewPager;
import android.support.v4.view.ViewPager.OnPageChangeListener;
import android.support.v4.app.FragmentStatePagerAdapter;
import android.support.v4.app.FragmentManager;
import android.support.v4.app.Fragment;
import android.util.Log;
import android.view.View;
import android.view.LayoutInflater;
import android.widget.ArrayAdapter;
import com.actionbarsherlock.app.*;
import com.actionbarsherlock.view.MenuInflater;
import com.actionbarsherlock.view.Menu;
import java.util.ArrayList;
import java.util.List;

abstract public class MannaActivity extends SherlockFragmentActivity 
                                    implements ActionBar.OnNavigationListener, 
                                               View.OnClickListener,
                                               ViewPager.OnPageChangeListener{

   protected static Canon theCanon = null;
   private static ArrayAdapter<MannaIntent> mannaHistory = null;
   private static int sLayout = android.R.layout.simple_list_item_1;

   @Override
   protected void onCreate(Bundle savedInstanceState) {
      super.onCreate(savedInstanceState);
      if(theCanon == null) theCanon = new Canon(getResources().getAssets());
      if(mannaHistory == null) mannaHistory = new ArrayAdapter(this, sLayout);

      /*Create action bar for history browsing support*/
      mannaBar = getSupportActionBar();
      mannaBar.setNavigationMode(ActionBar.NAVIGATION_MODE_LIST);
      mannaBar.setListNavigationCallbacks(mannaHistory, this);
      mannaBar.setDisplayShowTitleEnabled(false);

      /*Establish basic layout and page browsing support*/
      setContentView(R.layout.manna_browser);
      mPager = (ViewPager)findViewById(R.id.pager);
      mPager.setAdapter(new MannaAdapter(getSupportFragmentManager()));
      mPager.setOnPageChangeListener(this);

      /*Make the activities inflater available for sub activities*/
      inflater = getLayoutInflater();
   }
   protected ViewPager mPager;
   private ActionBar mannaBar;
   protected LayoutInflater inflater;

   protected void onStart() {
      super.onStart();
      updateHistory(mannaIntent());
   }

   public int pageIndex(int num) { 
      mPager.setCurrentItem(num); return pageIndex(); }
   public int pageIndex() { return mPager.getCurrentItem(); }
   public int page(int num) { mPager.setCurrentItem(num-1); return page(); }
   public int page() { return mPager.getCurrentItem()+1; }
   public void onPageScrollStateChanged(int state) {}
   public void onPageScrolled(int pos, float pOffset, int pOffPix) {}
   public void onPageSelected(int pos) { updateHistory(mannaIntent()); }

   class MannaAdapter extends FragmentStatePagerAdapter {
     public MannaAdapter(FragmentManager fm) { super(fm); }

     @Override
     public int getCount() { return getMannaFragCount(); }

     @Override
     public Fragment getItem(int position) {
         return getMannaFragment(position);
     }
   }

   protected MannaIntent mannaIntent() { return new MannaIntent(getIntent()); }

   abstract protected int getMannaFragCount();
   abstract protected Fragment getMannaFragment(int position);

   public void onClick(View v) { };

   public boolean onNavigationItemSelected(int itemPosition, long itemId) {
      MannaIntent navIntent = mannaHistory.getItem(itemPosition);
      MannaIntent curIntent = mannaIntent();
      Log.i("MA", "NavIntent: " + navIntent);
      Log.i("MA", "curIntent: " + curIntent);
      if(!curIntent.equals(navIntent)) startActivity(navIntent); 
      return true;  
   }

   public ArrayAdapter<MannaIntent> updateHistory(MannaIntent breadCrumb) {
      Log.i("MA", "Removing breadCrumb: " + breadCrumb);
      mannaHistory.remove(breadCrumb);
      Log.i("MA", "After removal: " + mannaHistory);
      mannaHistory.insert(breadCrumb, 0);
      Log.i("MA", "After insertion: " + mannaHistory);
      //mannaBar.setSelectedNavigationItem(0);
      //mannaHistory.notifyDataSetChanged();
      return mannaHistory;
   }

   /*
   @Override
   public boolean onCreateOptionsMenu(Menu menu) {
      MenuInflater inflater = getSupportMenuInflater();
      inflater.inflate(R.menu.manna_menu, menu);
      return true;
   }

   public void showManna(MannaIntent shewBread) {
      int layoutId = shewBread.getIntExtra("layout", R.layout.manna_browser);
      Log.i("MA", "Setting content view");
      setContentView(layoutId);
   }

   */
}

