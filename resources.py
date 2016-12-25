import os, re, fnmatch
from datetime import date
import urllib 

class PathResource(object):
    def __init__(self, path, name=None):
        self.path = path
        self.name = name or os.path.basename(path)

    @property
    def subpaths(self):
        spaths = []
        for root, dirs, files in os.walk(self.path):
            for d in dirs:
                spaths.append(os.path.join(root,d))
            for f in files:
                spaths.append(os.path.join(root,f))
        return spaths

    @property
    def directories(self):
        return filter(os.path.isdir, self.subpaths)

    @property
    def files(self):
        return filter(os.path.isfile, self.subpaths)

    @property
    def age(self):
        pathModTime=os.path.getmtime(self.path)
        uploadDate=date.fromtimestamp(pathModTime)
        pathage = date.today() - uploadDate
        return pathage.days

    def filesMatching(self, match):
        return fnmatch.filter(self.files, match)

    def  __str__(self):
        return self.name

    def  __repr__(self):
        return self.path

class Lesson(PathResource):
    @property
    def series(self):
        return os.path.basename(os.path.dirname(self.path))

    @property
    def tags(self):
        import mutagen.mp4
        return mutagen.mp4.Open(self.path)

    @property
    def rurl(self):
        return urllib.quote(os.path.join(self.series, self.name))

class Series(PathResource):
    limit = None

    @property
    def lessons(self, named=None):
        l = [ Lesson(x) for x in self.filesMatching("*.mp4") ]
        #by default a Series of lessons is sorted numerically by age
        l.sort(key=lambda l: l.age)
        #then optionally limited
        if self.limit:
            l = l[:self.limit]
        #and finally sorted alphabetically by name
        l.sort(key=lambda l: l.name)
        return l

    def lesson(self, named=None):
        if named:
            namedLesson = { l.name:l for l in self.lessons }[named]
            return namedLesson

    def normalize(self, dlen=None):
        """ normalize the series by renaming the lesson files.

            The lesson files of the series are renamed so that there are no
            spaces and the lesson numbers in each file name are padded with
            zeros so that they all have the same number of digits.
        """
        if not dlen: dlen=len(str(len(self)))
        dlimitPat = "%%0.%dd" % dlen
        def dlimit(x):
            return dlimitPat % int(x.group())
        dPat = re.compile(ur'(\d+)')
        for lesson in self.lessons:
            spacelessFile = os.path.basename(lesson.path).replace(" ", "")
            normfile = re.sub(dPat, dlimit, spacelessFile, count=1)
            opath = lesson.path
            npath = os.path.join(self.path, normfile)
            #If the original path is different from the normalized path
            if opath != npath: 
                #and if they both share the same directory
                if os.path.dirname(opath) == os.path.dirname(npath):
                    #and if the normalized path does NOT already exist
                    if not os.path.exists(npath):
                        #then rename the original path to the normalized path
                        os.rename(opath, npath)
                        print "Renamed %s to %s" % (opath, npath)
                    else:
                        print "Refused to clobber %s with %s" % (npath, opath)

    def sortBy(self, attr_name):
        pass

    def __len__(self):
        return len(self.lessons)

class Catalog(PathResource):

    @property
    def latest(self):
        series = Series(self.path, name="Latest Lessons")
        series.sortBy('upload_date')
        series.limit=10
        return series

    def series(self, named=None):
        if named:
            if named == 'latest':
                return self.latest
            else:
                namedSeries = { ser.name:ser for ser in self.series() }[named]
                #Normalizing the series ensures all lessons are properly named
                namedSeries.normalize()
                return namedSeries
        else:
            return [ Series(x) for x in self.directories ]

class Scripture(PathResource):
   def __init__(self, path):
      PathResource.__init__(self, path)
      
      self.pentatuch = self._initBooks("Genesis,Exodus,Leviticus",
                                       "Numbers,Deuteronomy")
      self.history   = self._initBooks("Joshua,Judges,Ruth,1stSamuel,2ndSamuel",
                                       "1stKings,2ndKings",
                                       "1stChronicles,2ndChronicles",
                                       "Ezra,Nehemia,Esther")
      self.poetry    = self._initBooks("Job,Psalms,Proverbs",
                                       "Ecclesiastes,Song of Solomon")
      self.major     = self._initBooks("Isaiah,Jeremiah,Lamentations",
                                       "Ezekiel,Daniel")
      self.minor     = self._initBooks("Hosea,Joel,Amos,Obadiah,Jonah,Micah",
                                       "Nahum,Habakkuk,Zephaniah,Haggai",
                                       "Zechariah,Malachi")
      self.gospels   = self._initBooks("Matthew,Mark,Luke,John")
      self.acts      = Book(os.path.join(self.path,"Acts.txt"))
      self.epistles  = self._initBooks("Romans,1stCorinthians,2ndCorinthians",
                                       "Galatians,Ephesians,Philippians",
                                       "Colossians,1stThessalonians",
                                       "2ndThessalonians,1stTimothy,2ndTimothy",
                                       "Titus,Philemon,Hebrews,James,1stPeter",
                                       "2ndPeter,1stJohn,2ndJohn,3rdJohn,Jude",
                                       "Revelation")
      self.oldTestament = self.pentatuch \
                        + self.history \
                        + self.poetry \
                        + self.major \
                        + self.minor
      self.newTestament = self.gospels \
                        + [self.acts] \
                        + self.epistles
      self.canon = self.oldTestament + self.newTestament
    
   def _initBooks(self, *names):
      bookset = []
      for nameset in names:
         nameset = [ x+".txt" for x in nameset.split(',') ]
         for name in nameset:
            book = Book(os.path.join(self.path,name))
            bookset.append(book)
            setattr(self, book.name, book)
      return bookset

   def book(self, bname):
      return getattr(self, bname)

import re
class Book(PathResource):
   def __init__(self, path):
      PathResource.__init__(self, path)
      self.name = os.path.splitext(os.path.basename(path))[0]
      self.text = open(self.path, 'r').read()

   def __len__(self):
      cre = re.compile(r'^\d+(?=:1\D+.*$)', re.DOTALL|re.MULTILINE) 
      return int(re.findall(cre, self.text)[-1])

   def chapter(self, cnum):
      if cnum > len(self): cnum = 1
      res = r'^%d:\d+.*?\D+(?=%d|%d:\d+)' % (cnum, cnum, cnum+1)
      cre = re.compile(res, re.DOTALL|re.MULTILINE)
      lines = re.findall(cre, self.text)
      class Chapter(object):
         def __init__(cself, clines):
            cself.number = int(re.match(r'^(\d+):', clines[0]).group(1))
            cself.verses = clines
         def __len__(cself): return len(cself.verses)
      return Chapter(lines)

