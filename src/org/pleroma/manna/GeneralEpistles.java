package org.pleroma.manna;
import java.util.*;

public class GeneralEpistles extends Division{

   GeneralEpistles(NewTestament source) { 
      super(source.filterBy(BOOKS));
   }

   public static final List<String> BOOKS 
      = Arrays.asList(  "James", "1stPeter", "2ndPeter", "Hebrews",
                        "1stJohn", "2ndJohn", "3rdJohn", "Jude");

   public String toString() { return "General Epistles"; }
}
