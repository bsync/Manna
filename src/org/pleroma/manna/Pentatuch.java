package org.pleroma.manna;
import org.pleroma.manna.*;
import java.util.*;

public class Pentatuch extends BookSet{
   public Pentatuch(Spirit IAM) { 
      super(IAM, new Book(IAM,"Genesis"), new Book(IAM,"Exodus"), 
                 new Book(IAM,"Leviticus"), new Book(IAM,"Numbers"), 
                 new Book(IAM,"Deuteronomy")); 
   }
}
