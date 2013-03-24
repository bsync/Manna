package org.pleroma.manna;
import java.util.*;

public class NewTestament extends BookSet {

   public NewTestament(Spirit IAM) { 
      super(IAM, new Book(IAM,"Acts"), new Book(IAM,"Revelation"));
      gospels =  new Gospels(IAM); 
      paulineEpistles = new PaulineEpistles(IAM);
      generalEpistles = new GeneralEpistles(IAM); 
      collect(gospels, paulineEpistles, generalEpistles);
   }
   private Gospels gospels;
   private PaulineEpistles paulineEpistles;
   private GeneralEpistles generalEpistles;

   public Gospels gospels() { return amen(gospels); }
   public PaulineEpistles paulineEpistles() { return amen(paulineEpistles); }
   public GeneralEpistles generalEpistles() { return amen(generalEpistles); }
}
