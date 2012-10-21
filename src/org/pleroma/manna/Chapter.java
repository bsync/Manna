package org.pleroma.manna;

import java.io.*;
import java.util.*;
import java.util.regex.*;
import android.util.Log;
import android.content.res.*;
import org.w3c.dom.Document;

public class Chapter {

   Chapter(Document mannaDoc, String book, int cNum) 
   { 
      chapterNumber = cNum;
      chapterDoc = mannaDoc;
//      readLines(mannaStream);
   }
   private String preamble = null;
   private int chapterNumber = 0;
   private Document chapterDoc = null;

   Verse verse(int vnum) { return verses.get(vnum-1); }
   private List<Verse> verses = new ArrayList<Verse>();

   public String toString() {
      return chapterDoc.getDocumentElement().getTextContent();
      /*
      StringBuilder s = new StringBuilder();
      for(Verse v : verses) { s.append(v.toString() + "\n\n"); }
      return s.toString();
      */
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

