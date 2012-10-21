package org.pleroma.manna;
import java.util.*;

public class Division extends LinkedHashMap<String, Canon.Manna> {

   Division() { super(); }
   Division(Division copySource) { 
      super(copySource); 
      books = new ArrayList(values());
   }
   List<Canon.Manna> books;

   public Division filterBy (List<String> l) {
      Division newDivision = new Division(this);
      newDivision.keySet().retainAll(l);
      return newDivision;
   }

   Canon.Manna book(int i) { return get(CANON.get(i-1)); }
   Canon.Manna book(String bookName) { return get(bookName); }

   public static final List<String> OLD_TESTAMENT 
      = Arrays.asList("Genesis", "Exodus", "Leviticus", "Numbers",
            "Deuteronomy", "Joshua", "Judges", "Ruth", "1stSamuel",
            "2ndSamuel", "1stKings", "2ndKings", "1stChronicles",
            "2ndChronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalm",
            "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah",
            "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel",
            "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
            "Zephaniah", "Haggai", "Zechariah", "Malachi");

   public static final List<String> NEW_TESTAMENT 
      = Arrays.asList("Matthew", "Mark", "Luke", "John", "Acts", "Romans",
            "1stCorinthians", "2ndCorinthians", "Galatians", "Ephesians",
            "Philippians", "Colossians", "1stThessalonians",
            "2ndThessalonians", "1stTimothy", "2ndTimothy", "Titus",
            "Philemon", "Hebrews", "James", "1stPeter", "2ndPeter", "1stJohn",
            "2ndJohn", "3rdJohn", "Jude", "Revelation");

   public static final List<String> CANON 
      = new ArrayList<String>(OLD_TESTAMENT);
      {  CANON.addAll(NEW_TESTAMENT); }

}

