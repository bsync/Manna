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

    public void testAment() {
       OldTestament oldTestament = theCanon.oldTestament;
       NewTestament newTestament = theCanon.newTestament;

       assertEquals(39, oldTestament.books.size());
       assertEquals(27, newTestament.books.size());
       assertEquals("Genesis", oldTestament.book(1).whatIsIt);
       assertEquals("Genesis", oldTestament.books.get(0).whatIsIt);

       Canon.Manna genesis = oldTestament.book("Genesis");
       assertTrue("Genesis".equals(genesis.whatIsIt));

       /*

       assertEquals(50, genesis.chapters.count);
       Chapter g1 = genesis.chapter(1);
       assertEquals(51, g1.verses.count);
       Verse g1v1 = g1.verse(1);
       assertNotNull(g1v1);

       assertTrue(g1v1.match("1 In the beginning"));
       Verse g1v31 = genesis.chapter(1).verse(31);
       assertTrue(g1v31.match("the sixth day."));
       */
//       Canon.Manna revelation =  newTestament.book("Revelation");
//       assertEquals(22, revelation.chapters.count);
    }
}
