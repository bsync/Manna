package org.pleroma.manna;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import java.util.ArrayList;
import java.util.regex.*;

public class MannaIntent extends Intent {
   MannaIntent(Intent i) { super(i); }

   MannaIntent(Context c, Manna m, Class<?> comClass) {
      super(c, comClass);
      Log.i("MI", "Using putExtra with " + m.toString());
      putExtra("MannaXref", m.toString());
   }

   public String name() {
      String mannaXref = toString();
      mannaXref = mannaXref.split("\\b")[1];
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
