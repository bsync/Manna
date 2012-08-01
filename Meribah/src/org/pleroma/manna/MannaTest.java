package org.pleroma.manna;

import android.test.AndroidTestCase;
import java.io.*;

public class MannaTest extends AndroidTestCase{

    public MannaTest() { super(); }

    protected void setUp() throws Exception {
        super.setUp();
        theCanon = new Canon(mContext.getResources().getAssets());
        assertNotNull(theCanon);
    }
    private Canon theCanon;

    public void testManna() throws IOException {
       Canon.Manna genesis = theCanon.selectManna("Genesis");
       assertNotNull(genesis);

       assertTrue("Unexpected name: " + genesis.whatIsIt(), 
                  "Genesis".equals(genesis.whatIsIt()));

       String g11 = genesis.chapter(1).verse(1).toString();
       assertNotNull(g11);
       assertTrue("No prefix of " + g11 + " matches \"1 In the beginning\"",
                  "1 In the beginning".equals(
                     g11.substring(0, "1 In the beginning".length())));

       String g131 = genesis.chapter(1).verse(31).toString();
       assertTrue("No suffix of " + g131 + " matches \"the sixth day.\"",
                  "the sixth day.".equals(
                     g131.substring(g131.length()-"the sixth day.".length())));
    }
}
