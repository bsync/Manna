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
#thru large files. Perl is well suited for pre-processing these text files.
use File::Path;
use XML::Writer;

$infile = ($ARGV[0]) ? $ARGV[0] : "preproc/*.txt";
foreach $filename (<${infile}>) {
   open ($file, "<", $filename) or die "Could not open $filename";
   $filename =~ m/(?:.*\/)?(.*)\.txt/; 
   print "Processing $filename ...";
   process_book($file, "assets/KJV/" . $1, $1);
   close $file;
   print "produced assets/KJV/$1\n";
}

sub process_book {
   my $infile = shift;
   my $bookpath = shift; rmtree($bookpath); mkpath($bookpath);
   my $bookname = shift; 
   my $chapter=1;

   #Iterate over verse text
   my $verseText = "";
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

   process_info_file($infile, $bookpath, $bookname, $chapter);
}

sub process_info_file {
   my $infile = shift;
   my $bookpath = shift; 
   my $bookname = shift;
   my $chptcnt = shift;

   #Start an info file containing just the title of the book for now
   open ($bfile, ">", "$bookpath/info.xml") 
      or die "Could not open $bookpath/info.xml";
   my $writer = XML::Writer->new(OUTPUT=>$bfile);
   $writer->xmlDecl();
   $writer->startTag("BookInfo", 'name'=>$bookname, 'chapters'=>$chptcnt);
   $writer->characters("\n\t");
   $writer->startTag("Title");
   my $titleLine = scalar <$infile>;
   $titleLine =~ s/\[.*\]:\s*//; $titleLine =~ s/$//; chomp($titleLine);
   $writer->characters($titleLine); 
   $writer->endTag("Title");
   $writer->characters("\n");
   $writer->endTag("BookInfo");
   $writer->end();
   close $bfile;
}

sub process_chapter {
   my $bookpath = shift; 
   my $ch = shift; 
   my $vText = shift;

   open ($cfile, ">", "$bookpath/$ch.txt") 
      or die "Could not open $bookpath/$ch.txt";
   $bookpath =~ /.*\/(.*)/;
   my $writer = XML::Writer->new(OUTPUT=>$cfile);
   $writer->xmlDecl();
   $writer->startTag("Chapter", 'number' => $ch);
   $writer->characters("\n");
#   print $cfile "Book $1 : Chapter $ch\n\n";

   @cvt = split /$ch:(\d+)/, $vText; 
   shift @cvt;
   while(@cvt) {
      ($vnum, $vtext, @cvt) = @cvt;
      $writer->startTag("Verse", 'number' => $vnum);
      $writer->characters($vtext);
#      print $cfile "$vnum. $vtext\n";
      $writer->endTag("Verse");
      $writer->characters("\n");
   }
   $writer->endTag("Chapter");
   $writer->end();
   close $cfile
}
