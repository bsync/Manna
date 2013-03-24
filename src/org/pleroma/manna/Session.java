package org.pleroma.manna;
import java.util.*;
public class Session extends ArrayList<Manna> { 
   public Manna addManna(Manna m) { add(m); return m; }
}
