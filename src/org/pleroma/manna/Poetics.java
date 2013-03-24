package org.pleroma.manna;
import org.pleroma.manna.*;
import java.util.*;

public class Poetics extends BookSet{
   public Poetics(Spirit IAM) { 
      super(IAM, new Book(IAM,"Job"), new Book(IAM,"Psalms"), 
                 new Book(IAM,"Proverbs"), new Book(IAM,"Ecclesiastes"), 
                 new Book(IAM,"Song of Solomon"));
   }
}
