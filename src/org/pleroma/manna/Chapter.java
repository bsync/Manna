package org.pleroma.manna;

import java.io.*;
import java.util.*;
import java.util.regex.*;
import android.util.Log;
import android.content.res.*;
import org.w3c.dom.Document;
import org.w3c.dom.NodeList;
import org.w3c.dom.Node;

public class Chapter {

   Chapter(Document mannaDoc, String book, int cNum) 
   { 
      number = cNum;
      chapterDoc = mannaDoc;
      NodeList verseNodes = chapterDoc.getElementsByTagName("Verse");
      for(int i = 0; i < verseNodes.getLength(); i++) {
         verses.add(new Verse(verseNodes.item(i))); }
   }
   private String preamble = null;
   public final int number;
   private Document chapterDoc = null;
   private ArrayList<Verse> verses = new ArrayList();

   public int verseCount() { return verses.size(); }
   Verse verse(int vnum) { return verses.get(vnum-1); }
   
   public String toString() {
      StringBuilder s = new StringBuilder();
      int i=1;
      for(Verse v : verses) { s.append(i++ + v.toString() + "\n\n"); }
      return s.toString();
   }
}

