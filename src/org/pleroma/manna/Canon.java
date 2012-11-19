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

   public Canon(AssetManager iam) { 
      this.iam = iam;
      try {
         spirit = DocumentBuilderFactory.newInstance().newDocumentBuilder();
         for(String eachBookDir : BOOKS) {
            String eachBookPath = "KJV/" + eachBookDir + "/info.xml";
            Log.e("Canon", "parsing " + eachBookPath ); 
            Document eachBookInfo = spirit.parse(iam.open(eachBookPath));
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
      divisions = new LinkedHashMap<String, Division>();
      oldTestament=new OldTestament(this);
      divisions.put(oldTestament.toString(), oldTestament);
      divisions.putAll(oldTestament.divisions);
      newTestament=new NewTestament(this);
      divisions.put(newTestament.toString(), newTestament);
      divisions.putAll(newTestament.divisions);
   }
   private AssetManager iam;
   private DocumentBuilder spirit;
   public final NewTestament newTestament;
   public final OldTestament oldTestament;
   public final Map<String, Division> divisions;

   public class Manna {
      Manna(Document bookInfo) {
         whatIsIt = bookInfo.getDocumentElement().getAttribute("name");
      }
      final String whatIsIt;

      public Chapter chapter(int cnum) {
         if(!desert.containsKey(cnum)) {
            String chapterPath = whatIsIt + "/" + cnum + ".txt";
            Log.d("Manna", "Scanning chapter " + chapterPath);
            try {
               InputStream mannaStream = iam.open("KJV/" + chapterPath);
               Document mannaDoc = spirit.parse(mannaStream);
               Chapter rChap = new Chapter(mannaDoc, whatIsIt, cnum);
               desert.put(cnum, rChap);
               mannaStream.close(); 
            } catch (IOException ioe) {
               throw new RuntimeException(ioe);
            } catch (SAXException saxe) {
               throw new RuntimeException(saxe);
            } 
         }
         return desert.get(cnum);
      }
      private HashMap<Integer, Chapter> desert = new HashMap<Integer,Chapter>();

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

   public static final List<String> BOOKS 
      = new ArrayList<String>(OldTestament.BOOKS);
   {  BOOKS.addAll(NewTestament.BOOKS); }
}
