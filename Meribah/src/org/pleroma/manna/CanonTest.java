package org.pleroma.manna;

import android.test.AndroidTestCase;
import java.util.*;
import java.io.*;

public class CanonTest extends AndroidTestCase {

 public CanonTest() { super(); }

 protected void setUp() throws Exception{
   super.setUp();
   Spirit theHolySpirit = new Spirit(mContext.getResources().getAssets());
   testCanon = theHolySpirit.inspiredCanon;
   assertNotNull(testCanon);
 }
 private Canon testCanon;

 public void testCanon() {
   assertEquals("The Holy Bible", testCanon.whatIsIt());
   assertEquals(66, testCanon.count());
   assertEquals("Genesis", testCanon.select("Genesis").whatIsIt());
   assertEquals("Matthew", testCanon.select("Matthew").whatIsIt());

   Chapter m1 = testCanon.select("Matthew", 1);
   assertNotNull(m1);
   assertTrue("Mathew 1 mis-start: " + m1.whatIsIt().substring(0,50),
              m1.whatIsIt().startsWith("1 The book of the generation of"));

   Verse m1v1 = testCanon.select("Matthew", 1, 1); 
   assertNotNull(m1v1);
   assertTrue("Mathew 1:1 mis-start: " + m1v1.whatIsIt().substring(0,50),
              m1v1.whatIsIt().startsWith(" The book of the generation of"));
 }

 public void testAment() {
   OldTestament ot = testCanon.oldTestament();
   NewTestament nt = testCanon.newTestament();

   assertEquals(39, ot.count());
   assertEquals(27, nt.count());
   assertEquals("OldTestament", ot.whatIsIt());
   assertEquals("NewTestament", nt.whatIsIt());
 }

 public void testBookChapterVerse() {
   Book genesis = testCanon.select("Genesis");
   assertTrue("Genesis".equals(genesis.whatIsIt()));
   assertEquals(50, genesis.count());
   Chapter g1 = genesis.select(1);
   assertEquals(31, g1.count());
   Verse g1v1 = g1.select(1);
   assertNotNull(g1v1);
   assertTrue("Match " + g1v1 + " against 'In the beginning'",
              g1v1.match("In the beginning"));
 }

 public void testPentatuch() {
   Pentatuch pentatuch = testCanon.oldTestament().pentatuch();
   assertEquals(pentatuch.count(), 5);
   assertNotNull("Missing Genesis", pentatuch.select("Genesis"));
   assertNotNull("Missing Exodus", pentatuch.select("Exodus"));
   assertNotNull("Missing Leviticus", pentatuch.select("Leviticus"));
   assertNotNull("Missing Numbers", pentatuch.select("Numbers"));
   assertNotNull("Missing Deuteronomy", pentatuch.select("Deuteronomy"));
   assertNull("Found Joshua", pentatuch.select("Joshua"));
 }

 public void testHistorics() {
    Historics historics = testCanon.oldTestament().historics();
    assertEquals(historics.count(), 12);
    assertNotNull("Missing Joshua", historics.select("Joshua")); 
    assertNotNull("Missing Judges", historics.select("Judges"));
    assertNotNull("Missing Ruth", historics.select("Ruth"));
    assertNotNull("Missing 1st Samuel", historics.select("1stSamuel"));
    assertNotNull("Missing 2nd Samuel", historics.select("2ndSamuel"));
    assertNotNull("Missing 1st Kings", historics.select("1stKings"));
    assertNotNull("Missing 2nd Kings", historics.select("2ndKings"));
    assertNotNull("Missing 1st Chronicles", historics.select("1stChronicles"));
    assertNotNull("Missing 2nd Chronicles", historics.select("2ndChronicles"));
    assertNotNull("Missing Ezra", historics.select("Ezra"));
    assertNotNull("Missing Nehemiah", historics.select("Nehemiah"));
    assertNotNull("Missing Esther", historics.select("Esther"));
    assertNull("Found Job", historics.select("Job"));
 }

 public void testPoetics() {
    Poetics poetics = testCanon.oldTestament().poetics();
    assertEquals(poetics.count(), 5);
    assertNotNull("Missing Job", poetics.select("Job")); 
    assertNotNull("Missing Psalms", poetics.select("Psalms"));
    assertNotNull("Missing Proverbs", poetics.select("Proverbs"));
    assertNotNull("Missing Ecclesiastes", poetics.select("Ecclesiastes"));
    assertNotNull("Missing SOS", poetics.select("Song of Solomon"));
    assertNull("Found Isaiah", poetics.select("Isaiah"));
 }

 public void testMajorProphets() {
    MajorProphets majorProphets = testCanon.oldTestament().majorProphets();
    assertEquals(majorProphets.count(), 5);
    assertNotNull("Missing Isaiah", majorProphets.select("Isaiah")); 
    assertNotNull("Missing Jeremiah", majorProphets.select("Jeremiah"));
    assertNotNull("Missing Lamen...", majorProphets.select("Lamentations"));
    assertNotNull("Missing Ezekiel", majorProphets.select("Ezekiel"));
    assertNotNull("Missing Daniel", majorProphets.select("Daniel"));
    assertNull("Found Hosea", majorProphets.select("Hosea"));
 }

 public void testMinorProphets() {
    MinorProphets minorProphets = testCanon.oldTestament().minorProphets();
    assertEquals(minorProphets.count(), 12);
    assertNotNull("Missing Hosea", minorProphets.select("Hosea")); 
    assertNotNull("Missing Joel", minorProphets.select("Joel"));
    assertNotNull("Missing Amos", minorProphets.select("Amos"));
    assertNotNull("Missing Obadiah", minorProphets.select("Obadiah"));
    assertNotNull("Missing Jonah", minorProphets.select("Jonah"));
    assertNotNull("Missing Micah", minorProphets.select("Micah"));
    assertNotNull("Missing Nahum", minorProphets.select("Nahum"));
    assertNotNull("Missing Habakkuk", minorProphets.select("Habakkuk"));
    assertNotNull("Missing Zephaniah", minorProphets.select("Zephaniah"));
    assertNotNull("Missing Haggai", minorProphets.select("Haggai"));
    assertNotNull("Missing Zechariah", minorProphets.select("Zechariah"));
    assertNotNull("Missing Malachi", minorProphets.select("Malachi"));
    assertNull("Found Matthew", minorProphets.select("Matthew"));
 }

 //New Testament BookSets

 public void testGospels() {
    Gospels gospels = testCanon.newTestament().gospels();
    assertEquals(gospels.count(), 4);
    assertNotNull("Missing Matthew", gospels.select("Matthew")); 
    assertNotNull("Missing Mark", gospels.select("Mark"));
    assertNotNull("Missing Luke", gospels.select("Luke"));
    assertNotNull("Missing John", gospels.select("John"));
    assertNull("Found Romans", gospels.select("Romans"));
 }

 public void testPaulineEpistles() {
    PaulineEpistles paulines = testCanon.newTestament().paulineEpistles();
    assertEquals(paulines.count(), 13);
    assertNotNull("Missing Romans", paulines.select("Romans")); 
    assertNotNull("Missing 1stCorinth", paulines.select("1stCorinthians"));
    assertNotNull("Missing 2ndCorinth", paulines.select("2ndCorinthians"));
    assertNotNull("Missing Galatians", paulines.select("Galatians"));
    assertNotNull("Missing Ephesians", paulines.select("Ephesians"));
    assertNotNull("Missing Philippians", paulines.select("Philippians"));
    assertNotNull("Missing Colossians", paulines.select("Colossians"));
    assertNotNull("Missing 1stThess", paulines.select("1stThessalonians"));
    assertNotNull("Missing 2ndThess", paulines.select("2ndThessalonians"));
    assertNotNull("Missing 1stTimothy", paulines.select("1stTimothy"));
    assertNotNull("Missing 2ndTimothy", paulines.select("2ndTimothy"));
    assertNotNull("Missing Titus", paulines.select("Titus"));
    assertNotNull("Missing Philemon", paulines.select("Philemon"));
    assertNull("Found James", paulines.select("James"));
 }

 public void testGeneralEpistles() {
    GeneralEpistles generals = testCanon.newTestament().generalEpistles();
    assertEquals(generals.count(), 8);
    assertNotNull("Missing James", generals.select("James")); 
    assertNotNull("Missing Hebrews", generals.select("Hebrews")); 
    assertNotNull("Missing 1stPeter", generals.select("1stPeter"));
    assertNotNull("Missing 2ndPeter", generals.select("2ndPeter"));
    assertNotNull("Missing 1stJohn", generals.select("1stJohn"));
    assertNotNull("Missing 2ndJohn", generals.select("2ndJohn"));
    assertNotNull("Missing 3rdJohn", generals.select("3rdJohn"));
    assertNotNull("Missing Jude", generals.select("Jude"));
 }

 public void testDivisions() {
    List<BookSet> sDiv = testCanon.bookSets();
    assertEquals("Canon, bad division: " + sDiv, 12, sDiv.size());
    OldTestament ot = testCanon.oldTestament();
    sDiv = ot.bookSets();
    assertEquals("Canon, bad division: " + sDiv, 5, sDiv.size());
    Pentatuch p = ot.pentatuch();
    List<Book> bDiv = p.books();
    assertEquals("Canon, bad division: " + bDiv, 5, bDiv.size());
 }
}
