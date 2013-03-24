package org.pleroma.manna;
import android.util.Log;
import java.io.*;
import java.util.*;
import java.lang.reflect.*;

import javax.xml.parsers.*;
import org.xml.sax.SAXException;
import org.w3c.dom.*;

public class Book extends Manna<Chapter> {

   public Book(Spirit IAM, String name) { super(IAM);
      Document bookDoc = inspiration.parse(name + "/info.xml");
      bookInfo = bookDoc.getDocumentElement();
   }
   private Element bookInfo;

   public String whatIsIt() { return bookInfo.getAttribute("name"); }
   public String toString() { return whatIsIt(); }

   public int count() { 
      return Integer.parseInt(bookInfo.getAttribute("chapters")); 
   }

   public Chapter select(int cnum) { 
      Chapter selectedChapter;
      String chapterKey = Integer.toString(cnum);
      if(!basket.containsKey(chapterKey)) {
         selectedChapter = new Chapter(inspiration, whatIsIt(), cnum);
         basket.put(chapterKey, selectedChapter);
      }
      else selectedChapter = basket.get(chapterKey);
      return amen(selectedChapter);
   }
}
