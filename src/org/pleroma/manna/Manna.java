package org.pleroma.manna;
import java.util.*;
import android.util.Log;

public abstract class Manna<T extends Manna> {

   public Manna(Spirit IAM) { 
      inspiration = IAM; 
      basket = new HashMap<String, T>();
   }
   protected Spirit inspiration;
   protected HashMap<String, T> basket;

   public Manna(Spirit IAM, T ... provision) { 
      this(IAM);
      collect(provision);
   }

   public abstract String whatIsIt();
   public int count() { return basket.size(); }

   public int collect(T ... provision) { 
      for(T m : provision) {
         basket.put(m.key(), m);
      }
      return basket.size();
   }
   public List<T> divide() { 
      List<T> portion = new ArrayList();
      for(T m : basket.values()) {
         portion.add(m);
         portion.addAll(m.divide());
      }
      return portion;
   }

   public <R extends Manna> R amen(R m) {
      inspiration.session(m);
      return m;
   }

   protected String key() { return whatIsIt(); }
}
