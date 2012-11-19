package org.pleroma.manna;
import java.util.*;

public class Acts extends Division{

   Acts(NewTestament source) { 
      super(source.filterBy(BOOKS));
   }

   public static final List<String> BOOKS = Arrays.asList("Acts");

   public String toString() { return "Acts"; }
}
