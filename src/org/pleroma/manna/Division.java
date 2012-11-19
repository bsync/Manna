package org.pleroma.manna;
import java.util.*;

public class Division extends LinkedHashMap<String, Canon.Manna> {

   Division() { super(); }
   Division(Division copySource) { 
      super(copySource); 
      books = new ArrayList(values());
   }
   List<Canon.Manna> books;

   public Division filterBy (List<String> l) {
      Division newDivision = new Division(this);
      newDivision.keySet().retainAll(l);
      return newDivision;
   }

   Canon.Manna book(int i) { return get(Canon.BOOKS.get(i-1)); }
   Canon.Manna book(String bookName) { return get(bookName); }

   protected static final List<String> NAMES 
      = Arrays.asList("Old Testament", "New Testament"); 
}

