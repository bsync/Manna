package org.pleroma.manna;
import java.util.*;

public class Poetics extends Division{

   Poetics(OldTestament source) { 
      super(source.filterBy(BOOKS));
   }

   public static final List<String> BOOKS 
      = Arrays.asList("Job", "Psalms", "Proverbs",
                      "Ecclesiastes", "Song of Solomon");

   public String toString() { return "Poetics"; }
}
