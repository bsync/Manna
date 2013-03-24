package org.pleroma.manna;

import java.util.*;

public class Canon extends BookSet { 
   public Canon(Spirit IAM) { 
      super(IAM);
      oldTestament = new OldTestament(IAM);
      newTestament = new NewTestament(IAM);
      collect(oldTestament, newTestament);
   }
   private final OldTestament oldTestament;
   private final NewTestament newTestament;

   public OldTestament oldTestament() { return amen(oldTestament); }
   public NewTestament newTestament() { return amen(newTestament); }

   public String whatIsIt() { return "The Holy Bible"; }
   public Book oldTestament(String name) { return oldTestament.select(name); }
   public Book newTestament(String name) { return newTestament.select(name); }

   public int count() { return oldTestament.count() + newTestament.count(); }

   public Book select(String name) {
      Book canonBook = oldTestament.select(name);
      if(canonBook == null) canonBook = newTestament.select(name);
      return canonBook;
   }

   public Chapter select(String name, int cnum) {
      return select(name).select(cnum);
   }
   public Verse select(String name, int cnum, int vnum) {
      return select(name).select(cnum).select(vnum);
   }
}
