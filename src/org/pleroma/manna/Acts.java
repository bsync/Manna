package org.pleroma.manna;
import java.util.*;

public class Acts extends Manna{

   Acts(Spirit IAM) { super(IAM); }

   public int count() { return BOOKS.size(); }
   public String whatIsIt() { return "Acts"; }
   public static final List<String> BOOKS = Arrays.asList("Acts");

}
