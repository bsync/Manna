package org.pleroma.manna;
import java.util.*;

public class OldTestament extends Division{

   OldTestament(Canon source) { 
      super(source.filterBy(BOOKS));
      divisions = new LinkedHashMap<String, Division>();
      pentatuch = new Pentatuch(this);
      divisions.put(pentatuch.toString(), pentatuch);
      historics = new Historics(this);
      divisions.put(historics.toString(), historics);
      poetics = new Poetics(this);
      divisions.put(poetics.toString(), poetics);
      majorProphets = new MajorProphets(this);
      divisions.put(majorProphets.toString(), majorProphets);
      minorProphets = new MinorProphets(this);
      divisions.put(minorProphets.toString(), minorProphets);
   }
   public final Pentatuch pentatuch;
   public final Historics historics;
   public final Poetics poetics;
   public final MajorProphets majorProphets;
   public final MinorProphets minorProphets;
   public final Map<String, Division> divisions;

   public static final List<String> BOOKS 
      = Arrays.asList("Genesis", "Exodus", "Leviticus", "Numbers",
            "Deuteronomy", "Joshua", "Judges", "Ruth", "1stSamuel",
            "2ndSamuel", "1stKings", "2ndKings", "1stChronicles",
            "2ndChronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalms",
            "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah",
            "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel",
            "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
            "Zephaniah", "Haggai", "Zechariah", "Malachi");

   public String toString() { return "Old Testament"; }
}
