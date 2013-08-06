package org.pleroma.manna;
import org.pleroma.manna.*;
import java.util.*;

public class GeneralEpistles extends BookSet {
   public GeneralEpistles(Spirit IAM) { 
      super(IAM, new Book(IAM, "James"), new Book(IAM, "1stPeter"), 
                 new Book(IAM, "2ndPeter"), new Book(IAM, "Hebrews"),
                 new Book(IAM, "1stJohn"), new Book(IAM, "2ndJohn"),
                 new Book(IAM, "3rdJohn"), new Book(IAM, "Jude"));
   }
}
