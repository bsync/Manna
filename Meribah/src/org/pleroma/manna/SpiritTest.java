package org.pleroma.manna;

import android.test.AndroidTestCase;
import java.util.*;
import java.io.*;

public class SpiritTest extends AndroidTestCase {

 public SpiritTest() { super(); }

 protected void setUp() throws Exception {
   super.setUp();
   theHolySpirit = new Spirit(mContext.getResources().getAssets());
 }
 private Spirit theHolySpirit;

 public void testCanon() {
    assertNotNull(theHolySpirit.inspiredCanon);
 }

 public void testParsing() {
    theHolySpirit.parse("Genesis/info.xml");
 }

 public void testSession() {
   Session history = theHolySpirit.session();
   assertNotNull(history);

   assertEquals(0, history.size());
   OldTestament ot = theHolySpirit.inspiredCanon.oldTestament();
   assertEquals(1, history.size());

   Pentatuch pt = ot.pentatuch();
   assertEquals(2, history.size());

   pt.select("Genesis");
   assertEquals(3, history.size());

   ot.select("Genesis");
   assertEquals(4, history.size());

   assertNotNull(history.get(0));
   assertEquals("OldTestament", history.get(0).whatIsIt());
   assertNotNull("NULL value in history!", history.get(1));
   assertEquals("Pentatuch", history.get(1).whatIsIt());
   assertNotNull("NULL value in history!", history.get(2));
   assertEquals("Genesis", history.get(2).whatIsIt());
   assertNotNull("NULL value in history!", history.get(3));
   assertEquals("Genesis", history.get(3).whatIsIt());
 }

}
