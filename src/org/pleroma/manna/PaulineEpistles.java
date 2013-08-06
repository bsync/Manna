package org.pleroma.manna;
import org.pleroma.manna.*;
import java.util.*;

public class PaulineEpistles extends BookSet{
   public PaulineEpistles(Spirit IAM) { 
      super(IAM, new Book(IAM,"Romans"), 
            new Book(IAM,"1stCorinthians"), new Book(IAM,"2ndCorinthians"),
            new Book(IAM,"Galatians"), new Book(IAM,"Ephesians"), 
            new Book(IAM,"Philippians"), new Book(IAM,"Colossians"),
            new Book(IAM,"1stThessalonians"), new Book(IAM,"2ndThessalonians"),
            new Book(IAM,"1stTimothy"), new Book(IAM,"2ndTimothy"),
            new Book(IAM,"Titus"), new Book(IAM,"Philemon"));
   }
}
