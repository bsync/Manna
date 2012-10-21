package org.pleroma.manna;
import java.util.Collection;

public class NewTestament extends Division{

   NewTestament(Canon source) { 
      super(source.filterBy(Division.NEW_TESTAMENT));
   }
}
