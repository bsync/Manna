package org.pleroma.manna;

import android.util.Log;
import java.util.*;

public class Verse {
   Verse(String text) { 
      /*
      Scanner verseScanner = new Scanner(text);
      verseScanner.findWithinHorizon("(\\d+)\\s+",0);
      verse = Integer.parseInt(verseScanner.match().group(1));
      vText = verse + " " + verseScanner.findWithinHorizon("(?s).*",0);
      vText = vText.replace("\n", "");
      */
      vText = text;
      Log.i("Manna", "Verse text is " + vText);
   }
   private String vText;
   private int verse;

   public String toString() {  return vText; }
}

