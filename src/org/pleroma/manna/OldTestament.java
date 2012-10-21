package org.pleroma.manna;
import java.util.Collection;

public class OldTestament extends Division{

   OldTestament(Canon source) { 
      super(source.filterBy(Division.OLD_TESTAMENT));
   }
}
