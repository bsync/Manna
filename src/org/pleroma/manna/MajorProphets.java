package org.pleroma.manna;
import org.pleroma.manna.*;
import java.util.*;

public class MajorProphets extends BookSet {
   public MajorProphets(Spirit IAM) { 
      super(IAM, new Book(IAM,"Isaiah"), new Book(IAM,"Jeremiah"), 
                 new Book(IAM,"Lamentations"), new Book(IAM,"Ezekiel"), 
                 new Book(IAM,"Daniel"));
   }
}
