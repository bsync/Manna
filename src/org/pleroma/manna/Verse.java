package org.pleroma.manna;

import android.util.Log;
import java.util.*;
import java.lang.Integer;
import org.w3c.dom.Node;
import org.w3c.dom.Attr;

public class Verse {
   Verse(Node verseNode) { 
      vText=verseNode.getTextContent(); 
      Node vAttr = verseNode.getAttributes().getNamedItem("number");
      number=Integer.parseInt(vAttr.getNodeValue());
   }
   private String vText;
   public final int number;

   public boolean match(String matchText) {  return vText.contains(matchText); }
   public String toString() {  return vText; }
}

