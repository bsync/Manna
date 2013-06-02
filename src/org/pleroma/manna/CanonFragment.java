package org.pleroma.manna;

import org.pleroma.manna.R;
import android.content.res.*;
import android.os.Bundle;
import android.view.*;
import android.support.v4.app.*;
import android.widget.*;
import android.util.Log;
import java.io.*;
import java.util.*;

public class CanonFragment extends ListFragment {

   @Override
   public void onActivityCreated(Bundle savedInstanceState) {
      super.onActivityCreated(savedInstanceState);
      theCanon = new Canon(getResources().getAssets());
      ot = theCanon.oldTestament();
      nt = theCanon.newTestament();
      showManna(theCanon);
   }
   protected static Canon theCanon;
   private OldTestament ot;
   private NewTestament nt;

   public boolean showManna(Manna breadOfLife) {
      mannaActivity.memorize(new MannaIntent(breadOfLife, this)); 
      setListAdapter(new CanonAdapter(breadOfLife));
      return true;
   }

   private class CanonAdapter extends ArrayAdapter<Manna> {
      CanonAdapter(Manna bol) {
         super(getActivity(), R.layout.button, bol.manna());
      }
   }

}
