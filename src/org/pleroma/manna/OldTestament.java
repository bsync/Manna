package org.pleroma.manna;

public class OldTestament extends BookSet {
   public OldTestament(Spirit IAM) { 
      super(IAM);
      pentatuch = new Pentatuch(IAM);
      historics = new Historics(IAM); 
      poetics = new Poetics(IAM);
      majorProphets = new MajorProphets(IAM);
      minorProphets = new MinorProphets(IAM);
      bookSets(pentatuch, historics, poetics, majorProphets, minorProphets);
   }
   private Pentatuch pentatuch; 
   private Historics historics; 
   private Poetics poetics; 
   private MajorProphets majorProphets;
   private MinorProphets minorProphets;

   public Pentatuch pentatuch() { return amen(pentatuch); }
   public Historics historics() { return amen(historics); }
   public Poetics poetics() { return amen(poetics); }
   public MajorProphets majorProphets() { return amen(majorProphets); }
   public MinorProphets minorProphets() { return amen(minorProphets); }
}
