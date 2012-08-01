package org.pleroma.manna;

import org.pleroma.manna.R;
import android.content.res.*;
import android.util.Log;
import java.util.*;
import java.io.*;
import java.lang.reflect.*;

public class Canon { 
   public Canon(AssetManager staffOfLife) { 
      iam = staffOfLife;
      try {
         for(String eachBookName : iam.list("KJV")) {
            Manna eachBook = new Manna(this, eachBookName);
            desertMap.put(eachBookName, eachBook);
         }
      } catch(Exception ioe) { Log.e("Manna", "Unable to load data." ); }
   }
   private AssetManager iam;
   public Manna selectManna(String name) { return desertMap.get(name); }
   private LinkedHashMap<String, Manna> desertMap = new LinkedHashMap();

   public Map<String, Manna> oldTestament() {
      return filter(desertMap, oldTestamentBooks);
   }
   private LinkedHashMap<String, Manna> oldDesertMap = new LinkedHashMap();
   private final List<String> oldTestamentBooks 
      = Arrays.asList("Genesis", "Exodus", "Leviticus", "Numbers",
            "Deuteronomy", "Joshua", "Judges", "Ruth", "1stSamuel",
            "2ndSamuel", "1stKings", "2ndKings", "1stChronicles",
            "2ndChronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalm",
            "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah",
            "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel",
            "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
            "Zephaniah", "Haggai", "Zechariah", "Malachi");


   public Map<String, Manna> newTestament() {
      return filter(desertMap, newTestamentBooks);
   }
   private LinkedHashMap<String, Manna> newDesertMap = new LinkedHashMap();
   private final List<String> newTestamentBooks 
      = Arrays.asList("Matthew", "Mark", "Luke", "John", "Acts", "Romans",
            "1stCorinthians", "2ndCorinthians", "Galatians", "Ephesians",
            "Philippians", "Colossians", "1stThessalonians",
            "2ndThessalonians", "1stTimothy", "2ndTimothy", "Titus",
            "Philemon", "Hebrews", "James", "1stPeter", "2ndPeter", "1stJohn",
            "2ndJohn", "3rdJohn", "Jude", "Revelation");

   private Map<String, Manna> filter(Map<String, Manna> m, List<String> l) {
      LinkedHashMap<String, Manna> filteredMap = new LinkedHashMap(); 
      for(String s : l) { 
         if(m.containsKey(s)) { 
            filteredMap.put(s, m.get(s)); 
         }
      }
      return filteredMap;
   }

   public class Manna {
      Manna(Canon theCanon, String bookName) {
         mannaCanon = theCanon;
         mannaName = bookName;
      }
      private String mannaName;
      private Canon mannaCanon;

      public String whatIsIt() { return mannaName; } 

      public Chapter chapter(int cnum) throws IOException {
         if(!mannaMap.containsKey(cnum)) {
            String chapterPath = mannaName + "/" + cnum + ".txt";
            Log.d("Manna", "Scanning chapter " + chapterPath);
            InputStream mannaStream = iam.open("KJV/" + chapterPath);
            Chapter rChap = new Chapter(mannaStream, mannaName, cnum);
            mannaMap.put(cnum, rChap);
            mannaStream.close();
         }
         return mannaMap.get(cnum);
      }
      private HashMap<Integer, Chapter> 
         mannaMap = new HashMap<Integer, Chapter>();

      public int chapterCount() { 
         if (chapterCount == 0) {
            Log.d("Manna", "Counting chapters for KJV/" + mannaName);
            try { chapterCount = iam.list("KJV/" + mannaName).length; }
            catch (Exception e) { return 0; } 
         }
         return chapterCount;
      }
      private int chapterCount = 0;
   }
}
