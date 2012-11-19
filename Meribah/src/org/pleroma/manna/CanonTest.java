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

    public void testPentatuch() {
       Pentatuch pentatuch = theCanon.oldTestament.pentatuch;
       assertEquals(pentatuch.books.size(), 5);
       assertTrue("Missing Genesis", pentatuch.containsKey("Genesis"));
       assertTrue("Missing Exodus", pentatuch.containsKey("Exodus"));
       assertTrue("Missing Leviticus", pentatuch.containsKey("Leviticus"));
       assertTrue("Missing Numbers", pentatuch.containsKey("Numbers"));
       assertTrue("Missing Deuteronomy", pentatuch.containsKey("Deuteronomy"));
    }

    public void testHistorics() {
       Historics historics = theCanon.oldTestament.historics;
       assertEquals(historics.books.size(), 12);
       assertTrue("Missing Joshua", historics.containsKey("Joshua")); 
       assertTrue("Missing Judges", historics.containsKey("Judges"));
       assertTrue("Missing Ruth", historics.containsKey("Ruth"));
       assertTrue("Missing 1st Samuel", historics.containsKey("1stSamuel"));
       assertTrue("Missing 2nd Samuel", historics.containsKey("2ndSamuel"));
       assertTrue("Missing 1st Kings", historics.containsKey("1stKings"));
       assertTrue("Missing 2nd Kings", historics.containsKey("2ndKings"));
       assertTrue("Missing 1st Chronicles", 
                  historics.containsKey("1stChronicles"));
       assertTrue("Missing 2nd Chronicles", 
                  historics.containsKey("2ndChronicles"));
       assertTrue("Missing Ezra", historics.containsKey("Ezra"));
       assertTrue("Missing Nehemiah", historics.containsKey("Nehemiah"));
       assertTrue("Missing Esther", historics.containsKey("Esther"));
    }

    public void testPoetics() {
       Poetics poetics = theCanon.oldTestament.poetics;
       assertEquals(poetics.books.size(), 5);
       assertTrue("Missing Job", poetics.containsKey("Job")); 
       assertTrue("Missing Psalms", poetics.containsKey("Psalms"));
       assertTrue("Missing Proverbs", poetics.containsKey("Proverbs"));
       assertTrue("Missing Ecclesiastes", poetics.containsKey("Ecclesiastes"));
       assertTrue("Missing Song of Solomon", 
                  poetics.containsKey("Song of Solomon"));
    }

    public void testMajorProphets() {
       MajorProphets majorProphets = theCanon.oldTestament.majorProphets;
       assertEquals(majorProphets.books.size(), 5);
       assertTrue("Missing Isaiah", majorProphets.containsKey("Isaiah")); 
       assertTrue("Missing Jeremiah", majorProphets.containsKey("Jeremiah"));
       assertTrue("Missing Lamentations", 
                  majorProphets.containsKey("Lamentations"));
       assertTrue("Missing Ezekiel", majorProphets.containsKey("Ezekiel"));
       assertTrue("Missing Daniel", majorProphets.containsKey("Daniel"));
    }

    public void testMinorProphets() {
       MinorProphets minorProphets = theCanon.oldTestament.minorProphets;
       assertEquals(minorProphets.books.size(), 12);
       assertTrue("Missing Hosea", minorProphets.containsKey("Hosea")); 
       assertTrue("Missing Joel", minorProphets.containsKey("Joel"));
       assertTrue("Missing Amos", minorProphets.containsKey("Amos"));
       assertTrue("Missing Obadiah", minorProphets.containsKey("Obadiah"));
       assertTrue("Missing Jonah", minorProphets.containsKey("Jonah"));
       assertTrue("Missing Micah", minorProphets.containsKey("Micah"));
       assertTrue("Missing Nahum", minorProphets.containsKey("Nahum"));
       assertTrue("Missing Habakkuk", minorProphets.containsKey("Habakkuk"));
       assertTrue("Missing Zephaniah", minorProphets.containsKey("Zephaniah"));
       assertTrue("Missing Haggai", minorProphets.containsKey("Haggai"));
       assertTrue("Missing Zechariah", minorProphets.containsKey("Zechariah"));
       assertTrue("Missing Malachi", minorProphets.containsKey("Malachi"));
    }

    public void testAment() {
       OldTestament oldTestament = theCanon.oldTestament;
       NewTestament newTestament = theCanon.newTestament;

       assertEquals(39, oldTestament.books.size());
       assertEquals(27, newTestament.books.size());
       assertEquals("Genesis", oldTestament.book(1).whatIsIt);
       assertEquals("Genesis", oldTestament.books.get(0).whatIsIt);

       Canon.Manna genesis = oldTestament.book("Genesis");
       assertTrue("Genesis".equals(genesis.whatIsIt));
       assertEquals(50, genesis.chapterCount());
       Chapter g1 = genesis.chapter(1);
       assertEquals(31, g1.verseCount());
       Verse g1v1 = g1.verse(1);
       assertNotNull(g1v1);
       assertTrue("Unable to match 'In the beginning' against: " + g1v1,
                  g1v1.match("In the beginning"));
       /*
       Verse g1v31 = genesis.chapter(1).verse(31);
       assertTrue(g1v31.match("the sixth day."));
       */
//       Canon.Manna revelation =  newTestament.book("Revelation");
//       assertEquals(22, revelation.chapters.count);
    }

    public void testGospels() {
       Gospels gospels = theCanon.newTestament.gospels;
       assertEquals(gospels.books.size(), 4);
       assertTrue("Missing Matthew", gospels.containsKey("Matthew")); 
       assertTrue("Missing Mark", gospels.containsKey("Mark"));
       assertTrue("Missing Luke", gospels.containsKey("Luke"));
       assertTrue("Missing John", gospels.containsKey("John"));
    }

    public void testPaulineEpistles() {
       PaulineEpistles paulines = theCanon.newTestament.paulines;
       assertEquals(paulines.books.size(), 13);
       assertTrue("Missing Romans", paulines.containsKey("Romans")); 
       assertTrue("Missing 1stCorinthians", 
                  paulines.containsKey("1stCorinthians"));
       assertTrue("Missing 2ndCorinthians", 
                  paulines.containsKey("2ndCorinthians"));
       assertTrue("Missing Galatians", paulines.containsKey("Galatians"));
       assertTrue("Missing Ephesians", paulines.containsKey("Ephesians"));
       assertTrue("Missing Philippians", paulines.containsKey("Philippians"));
       assertTrue("Missing Colossians", paulines.containsKey("Colossians"));
       assertTrue("Missing 1stThessalonians", 
                  paulines.containsKey("1stThessalonians"));
       assertTrue("Missing 2ndThessalonians", 
                  paulines.containsKey("2ndThessalonians"));
       assertTrue("Missing 1stTimothy", paulines.containsKey("1stTimothy"));
       assertTrue("Missing 2ndTimothy", paulines.containsKey("2ndTimothy"));
       assertTrue("Missing Titus", paulines.containsKey("Titus"));
       assertTrue("Missing Philemon", paulines.containsKey("Philemon"));
    }

    public void testGeneralEpistles() {
       GeneralEpistles generalEpistles = theCanon.newTestament.generalEpistles;
       assertEquals(generalEpistles.books.size(), 8);
       assertTrue("Missing James", generalEpistles.containsKey("James")); 
       assertTrue("Missing Hebrews", generalEpistles.containsKey("Hebrews")); 
       assertTrue("Missing 1stPeter", generalEpistles.containsKey("1stPeter"));
       assertTrue("Missing 2ndPeter", generalEpistles.containsKey("2ndPeter"));
       assertTrue("Missing 1stJohn", generalEpistles.containsKey("1stJohn"));
       assertTrue("Missing 2ndJohn", generalEpistles.containsKey("2ndJohn"));
       assertTrue("Missing 3rdJohn", generalEpistles.containsKey("3rdJohn"));
       assertTrue("Missing Jude", generalEpistles.containsKey("Jude"));
    }

    public void testActs() {
       Acts acts = theCanon.newTestament.acts;
       assertEquals(acts.books.size(), 1);
       assertTrue("Missing Acts", acts.containsKey("Acts")); 
    }

    public void testRevelation() {
       Revelation revelation = theCanon.newTestament.revelation;
       assertEquals(revelation.books.size(), 1);
       assertTrue("Missing Revelation", revelation.containsKey("Revelation")); 
    }
}
