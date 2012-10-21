package org.pleroma.manna;

import org.pleroma.manna.R;
import android.content.res.*;
import android.util.Log;
import java.util.*;
import java.io.*;
import java.lang.reflect.*;
import javax.xml.parsers.*;
import org.xml.sax.SAXException;
import org.w3c.dom.*;

public class Canon extends Division { 
   public Canon(AssetManager staffOfLife) { 
      iam = staffOfLife;
      try {
         docBuilder = DocumentBuilderFactory.newInstance().newDocumentBuilder();
         for(String eachBookDir : Division.CANON) {
            String eachBookPath = "KJV/" + eachBookDir + "/info.xml";
            Log.e("Canon", "parsing " + eachBookPath ); 
            Document eachBookInfo = docBuilder.parse(iam.open(eachBookPath));
            Manna eachBook = new Manna(eachBookInfo);
            put(eachBookDir, eachBook);
         }
      } catch(ParserConfigurationException pce) {
         Log.e("Canon", "Unable to parse biblical data." ); 
         throw new RuntimeException(pce);
      } catch(Exception ioe) { 
         Log.e("Canon", "Unable to load biblical data." ); 
         throw new RuntimeException(ioe);
      }
      oldTestament=new OldTestament(this);
      newTestament=new NewTestament(this);
   }
   private AssetManager iam;
   private DocumentBuilder docBuilder;
   public final NewTestament newTestament;
   public final OldTestament oldTestament;

   public class Manna {
      Manna(Document bookInfo) {
         whatIsIt = bookInfo.getDocumentElement().getAttribute("name");
      }
      final String whatIsIt;

      public List<Chapter> chapters() { 
         return new ArrayList(mannaMap.values()); 
      }

      public Chapter chapter(int cnum) {
         if(!mannaMap.containsKey(cnum)) {
            String chapterPath = whatIsIt + "/" + cnum + ".txt";
            Log.d("Manna", "Scanning chapter " + chapterPath);
            try {
               InputStream mannaStream = iam.open("KJV/" + chapterPath);
               Document mannaDoc = docBuilder.parse(mannaStream);
               Chapter rChap = new Chapter(mannaDoc, whatIsIt, cnum);
               mannaMap.put(cnum, rChap);
               mannaStream.close(); 
            } catch (IOException ioe) {
               throw new RuntimeException(ioe);
            } catch (SAXException saxe) {
               throw new RuntimeException(saxe);
            } 
         }
         return mannaMap.get(cnum);
      }
      private HashMap<Integer, Chapter> 
         mannaMap = new HashMap<Integer, Chapter>();

      public int chapterCount() { 
         if (chapterCount == 0) {
            Log.d("Manna", "Counting chapters for KJV/" + whatIsIt);
            try { chapterCount = iam.list("KJV/" + whatIsIt).length; }
            catch (Exception e) { return 0; } 
         }
         return chapterCount - 1; //One of the files is the info file
      }
      private int chapterCount = 0;
   }
}
