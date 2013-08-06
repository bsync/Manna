package org.pleroma.manna;

import android.content.res.*;
import android.util.Log;
import java.util.Collections;
import java.util.*;
import javax.xml.parsers.*;
import org.xml.sax.SAXException;
import org.w3c.dom.*;

public class Spirit {

   public Spirit(AssetManager IAM) { 
      inspiration = IAM;
   }
   private AssetManager inspiration;

   protected Document parse(String path) {
      try {
         if(author == null) {
            author = DocumentBuilderFactory.newInstance().newDocumentBuilder();
         }
         return author.parse(inspiration.open("KJV/" + path));
      } 
      catch (Exception e) {
         throw new RuntimeException("Caught an evil spirit: " + e);
      }
   }
   private DocumentBuilder author = null;
}
