package org.pleroma.manna;
import java.util.*;

public class MajorProphets extends Division{

   MajorProphets(OldTestament source) { 
      super(source.filterBy(BOOKS));
   }

   public static final List<String> BOOKS 
      = Arrays.asList("Isaiah", "Jeremiah", "Lamentations",
                      "Ezekiel", "Daniel");

   public String toString() { return "Major Prophets"; }
}
