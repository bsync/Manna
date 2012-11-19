package org.pleroma.manna;
import java.util.*;

public class PaulineEpistles extends Division{

   PaulineEpistles(NewTestament source) { 
      super(source.filterBy(BOOKS));
   }

   public static final List<String> BOOKS 
      = Arrays.asList(  "Romans", "1stCorinthians", "2ndCorinthians",
                        "Galatians", "Ephesians", "Philippians", "Colossians",
                        "1stThessalonians", "2ndThessalonians",
                        "1stTimothy", "2ndTimothy",
                        "Titus", "Philemon");

   public String toString() { return "Pauline Epistles"; }
}
