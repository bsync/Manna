package org.pleroma.manna;
import java.util.*;

public class Gospels extends Division{

   Gospels(NewTestament source) { 
      super(source.filterBy(BOOKS));
   }

   public static final List<String> BOOKS 
      = Arrays.asList("Matthew", "Mark", "Luke", "John");

   public String toString() { return "Gospels"; }
}
