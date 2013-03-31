package org.pleroma.manna;
import java.util.*;
import android.util.Log;

public abstract class Manna<T extends Manna> {

   public Manna(Spirit IAM) { 
      inspiration = IAM; 
      basket = new LinkedHashMap<String, T>();
   }
   protected Spirit inspiration;
   protected LinkedHashMap<String, T> basket;

   public Manna(Spirit IAM, T ... provision) { 
      this(IAM);
      manna(provision);
   }

   public abstract String whatIsIt();
   public String toString() { return whatIsIt(); }
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

   public <R extends Manna> R amen(R m) {
      inspiration.session(m);
      return m;
   }

   protected String key() { return whatIsIt(); }
}
