package org.pleroma.manna;

import android.content.res.AssetManager;
import java.util.*;
import javax.xml.parsers.*;
import org.xml.sax.SAXException;
import org.w3c.dom.*;

public class Canon extends BookSet { 
   public Canon(AssetManager IAM) { 
      super(new Spirit(IAM));
      oldTestament = new OldTestament(inspiration);
      newTestament = new NewTestament(inspiration);
      bookSets(oldTestament);
      bookSets(oldTestament.bookSets());
      bookSets(newTestament);
      bookSets(newTestament.bookSets());
   }
   private final OldTestament oldTestament;
   private final NewTestament newTestament;

   public OldTestament oldTestament() { return oldTestament; }
   public NewTestament newTestament() { return newTestament; }
   public Book oldTestament(String name) { return oldTestament.select(name); }
   public Book newTestament(String name) { return newTestament.select(name); }

   public String whatIsIt() { return "The Holy Bible"; }
}
