package org.pleroma.manna;

import java.io.*;
import java.util.*;
import java.util.regex.*;
import android.util.Log;
import android.content.res.*;

public class Chapter {

   Chapter(InputStream mannaStream, String book, int cNum) throws IOException
   { 
      chapterNumber = cNum;
      readLines(mannaStream);
   }
   private String preamble = null;
   private int chapterNumber = 0;

   Verse verse(int vnum) { return verses.get(vnum-1); }
   private List<Verse> verses = new ArrayList<Verse>();

   public String toString() {
      StringBuilder s = new StringBuilder();
      for(Verse v : verses) { s.append(v.toString() + "\n\n"); }
      return s.toString();
   }

   private void readLines(InputStream lineStream) throws IOException {
      InputStreamReader streamReader = new InputStreamReader(lineStream);
      BufferedReader bufferedReader = new BufferedReader(streamReader);
      List<String> lines = new ArrayList<String>();
      String line = null;
      if(chapterNumber == 1) preamble = bufferedReader.readLine();
      while ((line = bufferedReader.readLine()) != null) {
         verses.add(new Verse(line));
      }
      bufferedReader.close();
 }

}

