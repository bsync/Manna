package org.pleroma.manna;

import android.util.Log;
import java.util.*;
import java.lang.Integer;
import org.w3c.dom.Node;
import org.w3c.dom.Attr;

public class Verse extends Manna {

   Verse(Spirit IAM, Node verseNode) { super(IAM);
      vText=verseNode.getTextContent(); 
      Node vAttr = verseNode.getAttributes().getNamedItem("number");
      number=Integer.parseInt(vAttr.getNodeValue());
   }
   private String vText;
   public final int number;

   public String whatIsIt() { return vText; }
   public int count() { return vText.length(); }

   public boolean match(String matchText) { return vText.contains(matchText); }
   protected String key() { return Integer.toString(number); }
}

