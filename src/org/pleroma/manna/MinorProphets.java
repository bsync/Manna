package org.pleroma.manna;
import java.util.*;

public class MinorProphets extends Division{

   MinorProphets(OldTestament source) { 
      super(source.filterBy(BOOKS));
   }

   public static final List<String> BOOKS 
      = Arrays.asList("Hosea", "Joel", "Amos",
                      "Obadiah", "Jonah", "Micah",
                      "Nahum", "Habakkuk", "Zephaniah",
                      "Haggai", "Zechariah", "Malachi");

   public String toString() { return "Minor Prophets"; }
}
