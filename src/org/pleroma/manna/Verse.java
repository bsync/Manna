package org.pleroma.manna;

import android.util.Log;
import java.util.*;
import java.lang.Integer;
import org.w3c.dom.Node;
import org.w3c.dom.Attr;

public class Verse extends Manna {

   Verse(Spirit IAM, String bookName, int chpNum, Node verseNode) { 
      super(IAM);
      bookRef = bookName;
      cNum = chpNum;
      vText=verseNode.getTextContent().trim(); 
      Node vAttr = verseNode.getAttributes().getNamedItem("number");
      number=Integer.parseInt(vAttr.getNodeValue());
      
   }
   private String bookRef;
   private String vText;
   public final int cNum, number;

   public String whatIsIt() { return number +  " " + vText; }
   public String toString() { return bookRef + " " + cNum + ":" + number; }
   public int count() { return vText.length(); }

   public boolean match(String matchText) { 
      return vText.contains(matchText); 
   }
   protected String key() { return Integer.toString(number); }
}

