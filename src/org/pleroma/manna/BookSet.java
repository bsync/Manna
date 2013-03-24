package org.pleroma.manna;
import java.util.*;

public abstract class BookSet extends Manna<Book> {
   public BookSet(Spirit IAM) { super(IAM); }
   public BookSet(Spirit IAM, Book ... set) { super(IAM, set); }

   public List<String> titles() { return new ArrayList(basket.keySet()); }

   public String whatIsIt() { return this.getClass().getSimpleName(); }

   public Book select(String name) { 
      Book selectedManna = basket.get(name); 
      return amen(selectedManna);
   }

   public int collect(BookSet ... provision) { 
      for(BookSet m : provision) {
         collect(m.divide().toArray(new Book[m.count()]));
      }
      return count();
   }
}
