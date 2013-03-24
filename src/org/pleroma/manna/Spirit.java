package org.pleroma.manna;

import android.content.res.*;
import android.util.Log;
import java.util.Collections;
import java.util.*;
import javax.xml.parsers.*;
import org.xml.sax.SAXException;
import org.w3c.dom.*;

public class Spirit extends HashMap<String, Manna> {

   public Spirit(AssetManager IAM) throws ParserConfigurationException { 
      iamSpirit = IAM;
      author = DocumentBuilderFactory.newInstance().newDocumentBuilder();
      inspiredCanon = new Canon(this); 
      session = new Session(); 
   }
   public final Canon inspiredCanon;
   private Session session;
   private AssetManager iamSpirit;
   private DocumentBuilder author;

   public Document parse(String path) {
      try {
         return author.parse(iamSpirit.open("KJV/" + path));
      } 
      catch (Exception e) {
         throw new RuntimeException("Evil spirit: " + e);
      }
   }

   public Manna get(String key) {
      Manna matchBook = super.get(key);
      if(matchBook != null) {
         session.add(matchBook);
      }
      return matchBook;
   }

   public String put(Manna value) {
//TODO: Might need to check this against an internal list of titles.
      super.put(value.whatIsIt(), value);
      return value.whatIsIt();
   }

   public Session session() { return this.session; }
   public Session session(Manna m) {session.addManna(m); return this.session;}
}
