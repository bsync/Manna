package org.pleroma.manna;

public class NewTestament extends BookSet {

   public NewTestament(Spirit IAM) { super(IAM); 
      gospels =  new Gospels(IAM); 
      paulineEpistles = new PaulineEpistles(IAM);
      generalEpistles = new GeneralEpistles(IAM); 
      ActSet acts = new ActSet(IAM);
      RevSet rev = new RevSet(IAM);
      bookSets(gospels, acts, paulineEpistles, generalEpistles, rev);
   }
   private Gospels gospels;
   private PaulineEpistles paulineEpistles;
   private GeneralEpistles generalEpistles;

   public Gospels gospels() { return amen(gospels); }
   public PaulineEpistles paulineEpistles() { return amen(paulineEpistles); }
   public GeneralEpistles generalEpistles() { return amen(generalEpistles); }

   private class ActSet extends BookSet{
      public ActSet(Spirit IAM) { super(IAM, new Book(IAM,"Acts")); }
      public String whatIsIt() { return "Acts"; }
   }
      
   private class RevSet extends BookSet{
      public RevSet(Spirit IAM) { super(IAM, new Book(IAM,"Revelation")); }
      public String whatIsIt() { return "Revelation"; }
   }
}
