package org.pleroma.manna;
import java.util.*;

public class Pentatuch extends Division{

   Pentatuch(OldTestament source) { 
      super(source.filterBy(BOOKS));
   }

   public static final List<String> BOOKS 
      = Arrays.asList("Genesis", "Exodus", 
                       "Leviticus", "Numbers",
                       "Deuteronomy");

   public String toString() { return "Torah"; }
}
