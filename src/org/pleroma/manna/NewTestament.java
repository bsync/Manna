package org.pleroma.manna;
import java.util.*;

public class NewTestament extends Division{

   NewTestament(Canon source) { 
      super(source.filterBy(BOOKS));
      divisions = new LinkedHashMap<String, Division>();
      gospels = new Gospels(this);
      divisions.put(gospels.toString(), gospels);
      acts = new Acts(this);
      divisions.put(acts.toString(), acts);
      paulines = new PaulineEpistles(this);
      divisions.put(paulines.toString(), paulines);
      generalEpistles = new GeneralEpistles(this);
      divisions.put(generalEpistles.toString(), generalEpistles);
      revelation = new Revelation(this);
      divisions.put(revelation.toString(), revelation);
   }
   public final Gospels gospels;
   public final PaulineEpistles paulines;
   public final GeneralEpistles generalEpistles;
   public final Acts acts;
   public final Revelation revelation;
   public final Map<String, Division> divisions;

   public static final List<String> BOOKS 
      = Arrays.asList("Matthew", "Mark", "Luke", "John", "Acts", "Romans",
            "1stCorinthians", "2ndCorinthians", "Galatians", "Ephesians",
            "Philippians", "Colossians", "1stThessalonians",
            "2ndThessalonians", "1stTimothy", "2ndTimothy", "Titus",
            "Philemon", "Hebrews", "James", "1stPeter", "2ndPeter", "1stJohn",
            "2ndJohn", "3rdJohn", "Jude", "Revelation");

   public String toString() { return "New Testament"; }
}
