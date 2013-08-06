package org.pleroma.manna;
import java.util.*;
import android.util.Log;

public class BookSet extends Manna<Book> {
   public BookSet(Spirit IAM) { super(IAM); }
   public BookSet(Spirit IAM, Book ... set) { super(IAM, set); }
   public List<String> titles() { return new ArrayList(basket.keySet()); }
   public String whatIsIt() { return this.getClass().getSimpleName(); }

   public Book select(String name) { return basket.get(name); }
   public Chapter select(String name, int cnum) {
      return select(name).select(cnum);
   }
   public Verse select(String name, int cnum, int vnum) {
      return select(name).select(cnum).select(vnum);
   }
   public List<Book> books(Book ... provision) { return manna(); }

   public BookSet selectSet(String name) { return setBasket.get(name); }
   public List<BookSet> bookSets(BookSet ... provision) { 
      return bookSets(Arrays.asList(provision));
   }
   public List<BookSet> bookSets(List<BookSet> provision) { 
      for(BookSet m : provision) {
         setBasket.put(m.key(), m);
         manna(m.books());
      }
      return new ArrayList(setBasket.values());
   }
   private LinkedHashMap<String, BookSet> setBasket 
      = new LinkedHashMap<String, BookSet>();
}
