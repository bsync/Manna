package org.pleroma.manna;
import java.util.*;
import android.util.Log;

public abstract class Manna<T extends Manna> {

   protected Manna(Spirit theHolySpirit, T ... provision) { 
      this(theHolySpirit);
      manna(provision); 
   }

   protected Manna(Spirit theHolySpirit) { 
      inspiration = theHolySpirit;
      basket = new LinkedHashMap<String, T>();
   }
   protected Spirit inspiration;
   protected LinkedHashMap<String, T> basket;

   public abstract String whatIsIt();
   public String toString() { return this.getClass().getSimpleName(); }
   public int count() { return basket.size(); }

   public T select(String key) { return basket.get(key); }

   public List<T> manna(T ... provision) { 
      return manna(Arrays.asList(provision));
   }
   public List<T> manna(List<T> provision) { 
      for(T m : provision) {
         basket.put(m.key(), m);
      }
      return new ArrayList(basket.values());
   }

   protected String key() { return whatIsIt(); }
}
