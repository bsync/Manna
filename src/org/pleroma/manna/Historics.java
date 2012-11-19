package org.pleroma.manna;
import java.util.*;

public class Historics extends Division{

   Historics(OldTestament source) { 
      super(source.filterBy(BOOKS));
   }

   public static final List<String> BOOKS 
      = Arrays.asList("Joshua", "Judges", "Ruth",
                      "1stSamuel", "2ndSamuel", "1stKings", "2ndKings",
                      "1stChronicles", "2ndChronicles",
                      "Ezra", "Nehemiah", "Esther");

   public String toString() { return "Historics"; }
}
