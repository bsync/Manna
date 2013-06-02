package org.pleroma.manna;
import android.os.Bundle;
import android.support.v4.app.*;
import android.widget.ArrayAdapter;

public class MannaFragment extends ListFragment {

   public void onActivityCreated(Bundle savedInstanceState) {
      super.onActivityCreated(savedInstanceState);
      mannaActivity = (MannaActivity) getActivity();
   }
   MannaActivity mannaActivity;

}
