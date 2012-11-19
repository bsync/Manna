package org.pleroma.manna;
import java.util.*;

public class Revelation extends Division{

   Revelation(NewTestament source) { 
      super(source.filterBy(BOOKS));
   }

   public static final List<String> BOOKS = Arrays.asList("Revelation");

   public String toString() { return "Revelation"; }
}
