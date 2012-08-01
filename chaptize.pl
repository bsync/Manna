#!/bin/perl
#This perl script is used to preprocess the data files for use by the Manna
#application. It expects to find one file per book in the 'preproc' directory.
#For each file it finds the script creates a subdirectory in the assets/KJV
#directory bearing the name of the book (ie...  the filename minus any
#extension). Inside this subdirectory the script writes one file per chapter as
#it parses them from the original file. The original file is expected to
#contain chapter markers of the form (^|\s)\d+:\d+\s ie...  the start of a line
#or at least one space followed by any number of digits for the chapter
#followed by a ':' followed by any number of digits for the verse followed by
#at least one space.
#
#Incidently, the main reason for doing this is to make it easier for the Manna
#application to navigate to a particular passage without requiring it to parse
#thru large files. Java, it seems, is not so well suited as perl for processing
#text files.
use File::Path;

$infile = ($ARGV[0]) ? $ARGV[0] : "preproc/*.txt";
foreach $filename (<${infile}>) {
   open ($file, "<", $filename) or die "Could not open $filename";
   $filename =~ m/(?:.*\/)?(.*)\.txt/; 
   print "Processing $filename ...";
   process_book($file, "assets/KJV/" . $1);
   close $file;
   print "produced assets/KJV/$1\n";
}

sub process_book {
   my $infile = shift;
   my $bookpath = shift; rmtree($bookpath); mkpath($bookpath);
   my $chapter=1;
   my $verseText = scalar <$infile>; #initialize with title line.
   while(<$infile>) {
      s/^\s*//; #Strip white space at start of line 
      s/\s*\r*\n$//; #Strip line endings and white space at line endings
      s/\s+/ /g; # Replace multiple internal spaces with just one.
      next if /^$/; #Skip empty lines 
      my $nextchapter=$chapter+1;
      if(/(^|.*\s+)($nextchapter:1\s+.*)/)  { #Detect chapter switch
         $verseText .= $1 if($1); #Include last bit of chapter
         process_chapter($bookpath, $chapter, $verseText);
         $verseText=$2; #Reinit verseText with first bit of next chapter
         $chapter++; #Start looking for next chapter
      }
      else { $verseText .= "$_ "; } #No chapter switch detected yet
   }
   #Handle the last chapter of book
   process_chapter($bookpath, $chapter, $verseText);
}

sub process_chapter {
   my $bookpath = shift; 
   my $ch = shift; 
   my $vText = shift;
   my @processed_text;

   open ($cfile, ">", "$bookpath/$ch.txt") 
      or die "Could not open $bookpath/$ch.txt";

   @cvt = split /($ch:\d+)/, $vText; 
   $leadingField = shift @cvt; 
   print $cfile "$leadingField \n" if ($ch == 1); #Print chapter1 titles
   while(@cvt) {
      ($cav, $vtext, @cvt) = @cvt;
      print $cfile "$cav $vtext\n";
   }

   close $cfile
}
