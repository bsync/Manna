package org.pleroma.manna;
import java.util.*;

public class Revelation extends Manna{

   Revelation(Spirit IAM) { super(IAM); }

   public int count() { return BOOKS.size(); }
   public String whatIsIt() { return "Revelation"; }
   public static final List<String> BOOKS = Arrays.asList("Revelation");

}
