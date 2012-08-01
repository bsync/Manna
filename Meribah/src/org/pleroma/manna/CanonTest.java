package org.pleroma.manna;

import android.test.AndroidTestCase;
import java.util.*;
import java.io.*;

public class CanonTest extends AndroidTestCase {

    public CanonTest() { super(); }

    protected void setUp() throws Exception {
        super.setUp();
        theCanon = new Canon(mContext.getResources().getAssets());
        assertNotNull(theCanon);
    }
    private Canon theCanon;

    public void testCanon() throws IOException {
       Map<String, Canon.Manna> oldTestament = theCanon.oldTestament();
       Map<String, Canon.Manna> newTestament = theCanon.newTestament();

       assertEquals("Incomplete Old Testament.", 39, oldTestament.size());
       assertEquals("Incomplete New Testament.", 27, newTestament.size());

       assertEquals("Genesis", oldTestament.keySet().iterator().next());

       Canon.Manna genesis = oldTestament.get("Genesis");
       assertNotNull("Canon missing Genesis: ", genesis);
       assertEquals("Missing chapters from Genesis.", 
                     50, genesis.chapterCount());

       Canon.Manna revelation =  newTestament.get("Revelation");
       assertNotNull("Canon missing Revelation.", revelation);
       assertEquals("Missing chapters from Revelation.", 
                    22, revelation.chapterCount());
    }

}
