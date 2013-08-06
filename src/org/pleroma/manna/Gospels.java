package org.pleroma.manna;
import org.pleroma.manna.*;
import java.util.*;

public class Gospels extends BookSet{
   public Gospels(Spirit IAM) { 
      super(IAM, new Book(IAM,"Matthew"), new Book(IAM,"Mark"), 
                 new Book(IAM,"Luke"), new Book(IAM,"John")); 
   }
}
