package org.pleroma.manna;

import java.io.*;
import java.util.*;
import java.util.regex.*;
import android.util.Log;
import android.content.res.*;
import org.w3c.dom.Document;
import org.w3c.dom.NodeList;
import org.w3c.dom.Node;

public class Chapter extends Manna<Verse> {

   Chapter(Spirit IAM, String bookName, int cNum) { super(IAM);
      number = cNum;
      String chapterPath = bookName + "/" + cNum + ".txt";
      Document chapterDoc = inspiration.parse(chapterPath);
      NodeList verseNodes = chapterDoc.getElementsByTagName("Verse");
      verses = new ArrayList();
      for(int i=0; i < verseNodes.getLength(); i++) {
         verses.add(new Verse(inspiration, verseNodes.item(i))); 
      }
      manna(verses.toArray(new Verse[verses.size()]));
   }
   public final int number;
   ArrayList<Verse> verses; 

   public String whatIsIt() {
      StringBuilder s = new StringBuilder();
      int i=1;
      for(Verse v : verses) { s.append(i++ + v.whatIsIt() + "\n\n"); }
      return s.toString();
   }
   public Verse select(int vnum) { 
      String verseKey = Integer.toString(vnum);
      return amen(basket.get(verseKey)); 
   }
   protected String key() { return Integer.toString(number); }
}

