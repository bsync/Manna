package org.pleroma.manna;
import org.pleroma.manna.*;
import java.util.*;

public class Historics extends BookSet{
   public Historics(Spirit IAM) { 
      super(IAM, new Book(IAM,"Joshua"), new Book(IAM,"Judges"), 
                 new Book(IAM,"Ruth"), new Book(IAM,"1stSamuel"), 
                 new Book(IAM,"2ndSamuel"), new Book(IAM,"1stKings"), 
                 new Book(IAM,"2ndKings"), new Book(IAM,"1stChronicles"), 
                 new Book(IAM,"2ndChronicles"), new Book(IAM,"Ezra"), 
                 new Book(IAM,"Nehemiah"), new Book(IAM,"Esther"));
   }
}
