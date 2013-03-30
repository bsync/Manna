package org.pleroma.manna;

import java.util.*;

public class Canon extends BookSet { 
   public Canon(Spirit IAM) { 
      super(IAM);
      oldTestament = new OldTestament(IAM);
      newTestament = new NewTestament(IAM);
      bookSets(oldTestament);
      bookSets(oldTestament.bookSets());
      bookSets(newTestament);
      bookSets(newTestament.bookSets());
   }
   private final OldTestament oldTestament;
   private final NewTestament newTestament;

   public OldTestament oldTestament() { return amen(oldTestament); }
   public NewTestament newTestament() { return amen(newTestament); }
   public Book oldTestament(String name) { return oldTestament.select(name); }
   public Book newTestament(String name) { return newTestament.select(name); }

   public String whatIsIt() { return "The Holy Bible"; }
}
