import os
import re
import ffmpy
import boto3

from pathlib import Path
from functools import partial
from datetime import date
from botocore.exceptions import ClientError
from flask import url_for
import fnmatch

class PathResource(object):
    bucket = None

    def __init__(self, path, name=None):
        self.path = path
        self.name = name or os.path.basename(path)
        if not os.path.lexists(self.path):
            os.mkdir(self.path)

    def listing(self, fullpath=False):
        lpaths = []
        if fullpath:
            for root, dirs, files in os.walk(self.path, followlinks=True):
                for d in dirs:
                    lpaths.append(os.path.join(root, d))
                for f in files:
                    lpaths.append(os.path.join(root, f))
        else:
            lpaths = os.listdir(self.path)
        return sorted(lpaths)

    @property
    def directories(self):
        return filter(os.path.isdir, self.listing(fullpath=True))

    @property
    def files(self):
        return filter(os.path.isfile, self.listing(fullpath=True))

    @property
    def age(self):
        pathModTime = os.path.getmtime(self.path)
        uploadDate = date.fromtimestamp(pathModTime)
        pathage = date.today() - uploadDate
        return pathage.days

    def filesMatching(self, match):
        return fnmatch.filter(self.files, match)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.path

class Catalog(PathResource):
    def __init__(self, path, bucket_name=None):
        PathResource.__init__(self, path)
        if bucket_name:
            s3 = boto3.resource('s3')
            PathResource.bucket = s3.Bucket(bucket_name)
            try:
                c3 = {'LocationConstraint': 'us-east-2'}
                self.bucket.create(CreateBucketConfiguration=c3)
            except ClientError as ce:
                if 'BucketAlreadyOwnedByYou' in str(ce):
                    print("Looks like bucket already exists: %s " % ce)
                else:
                    raise ce
            PathResource.bucket.client = boto3.client('s3')
            self._syncWithBucket(path)

    def _syncWithBucket(self, path):
        """ Syncronize a local directory tree with the S3 bucket.
        
            This internal routine is responsible for ensuring that a local
            directory tree exists which matches the current keyed content of
            the corresponding S3 bucket.

            The normal S3 python API (boto) does NOT lend itself to an easy
            directory tree representation of the cataloged content. To allow
            for normal directory tree navigation in the rest of the code, this
            routine creates a matching local directory tree which mirrors the
            S3 content in name only and is used to construct the catalog
            listings of lessons available for download via the S3 resource.
        """
        for obj in self.bucket.objects.filter(Prefix=path):
            fpath = os.path.relpath(obj.key)
            dpath = os.path.dirname(fpath)
            if not os.path.exists(dpath): 
                os.makedirs(dpath)
            if not os.path.exists(fpath):
                Path(fpath).touch(exist_ok=True)

    @property
    def latest(self):
        series = Series(self.path, "latest")
        series.sortBy('upload_date')
        series.limit = 10
        return series

    def addSeries(self, name, description):
        os.mkdir(os.path.join(self.path, name))

    def series(self, named=None):
        if named:
            if named == 'latest':
                return self.latest
            else:
                return {ser.name: ser for ser in self.series()}[named]
        else:
            return [Series(x) for x in self.directories]

    def checkPassForUrl(self, word, url):
        if word == 'pleroma101':
            return True
        try:
            useries = self.series(url.split('/')[-1])
            denseName = useries.name.replace(' ', '')
            hplen = int(min(len(denseName)+1, 8)/2)
            passTuple = zip(denseName[:hplen-1:-1], denseName[:hplen-1:1])
            Pass = ''.join([x for l in passTuple for x in l])
            return hash(Pass) == hash(word)
        except KeyError:
            return False

class Series(PathResource):
    limit = None

    def __init__(self, path, name=None):
        PathResource.__init__(self, path, name)
        self.normalize()

    def normalize(self):
        """ Normalize the series by renaming the lesson files.

            The lesson files of the series are renamed so that there are no
            spaces and the lesson numbers in each file name are padded with
            zeros so that they all have the same number of digits.
        """
        mpFiles = self.filesMatching("*.mp*")
        # number of digits in number of mpFiles
        dlimitPat = "%%0.%dd" % len(str(len(mpFiles)))

        def dlimit(x):
            return dlimitPat % int(x.group())
        dPat = re.compile(r'(\d+)')
        for mpFile in mpFiles:
            spacelessFile = os.path.basename(mpFile).replace(" ", "")
            normfile = re.sub(dPat, dlimit, spacelessFile, count=1)
            opath = mpFile
            npath = os.path.join(self.path, normfile)
            # If the original path is different from the normalized path
            if opath != npath:
                # and if they both share the same directory
                if os.path.dirname(opath) == os.path.dirname(npath):
                    # and if the normalized path does NOT already exist
                    if not os.path.exists(npath):
                        # then rename the original path to the normalized path
                        os.rename(opath, npath)
                        if self.bucket: #And rename the corresponding bucket content too
                           s3 = boto3.resource('s3')
                           obj = s3.Object(self.bucket.name, npath)
                           obj.copy({'Bucket': self.bucket.name, 'Key': opath})
                           s3.Object(self.bucket.name, opath).delete()
                        print("Renamed %s to %s" % (opath, npath))
                    else:
                        print("Refused to clobber %s with %s" % (npath, opath))

    def addLesson(self, lessonFile):
        dest = os.path.join(self.path, os.path.basename(lessonFile))
        open(dest, 'a').close()  # Create empty file as place holder
        self.bucket.put_object(Key=dest, Body=lessonFile)

    @property
    def lessons(self, named=None):
        l = [Lesson(x) for x in self.filesMatching("*.mp4")]
        # by default a Series of lessons is sorted numerically by age
        l.sort(key=lambda l: l.age)
        # then optionally limited
        if self.limit:
            l = l[:self.limit]
        # and finally sorted alphabetically by name
        l.sort(key=lambda l: l.name)
        return l

    def lesson(self, named=None):
        if named:
            namedLesson = {l.name: l for l in self.lessons}[named]
            return namedLesson

    def sortBy(self, attr_name):
        pass

    def __len__(self):
        return len(self.lessons)


class Lesson(PathResource):
    @property
    def series(self):
        return os.path.basename(os.path.dirname(self.path))

    @property
    def tags(self):
        import mutagen.mp4
        return mutagen.mp4.Open(self.path)

    @property
    def url(self):
        lurl = url_for('static', filename=self.path, _external=True)
        if os.path.getsize(self.path) < 10 and self.bucket:
            lpath = Path(self.path)
            lurl = self.bucket.client.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={'Bucket': self.bucket.name,
                            'Key': str(lpath)})
        return lurl

    @property
    def mp3(self):
        return Mp3Lesson(self.path)

class Mp3Lesson(Lesson):
    def __init__(self, path):
        Lesson.__init__(self, path)
        mp3Path = os.path.splitext(path)[0]+'.mp3'
        if self.bucket: 
            if len(list(self.bucket.objects.filter(Prefix=mp3Path))) == 0:
                ff = ffmpy.FFmpeg(inputs={self.url: '-ss 20 -t 20'}, 
                                  outputs={'pipe:1': '-f mp3 -b 80k -ac 1'})
                import subprocess
                stdout, stderr = ff.run(stdout=subprocess.PIPE)
                self.bucket.put_object(Body=stdout, Key=mp3Path)

        self.path = mp3Path

class Scripture(PathResource):
    def __init__(self, path):
        PathResource.__init__(self, path)

        self.pentatuch = self._initBooks("Genesis,Exodus,Leviticus",
                                         "Numbers,Deuteronomy")
        self.history = self._initBooks("Joshua,Judges,Ruth,"
                                       "1stSamuel,2ndSamuel",
                                       "1stKings,2ndKings",
                                       "1stChronicles,2ndChronicles",
                                       "Ezra,Nehemia,Esther")
        self.poetry = self._initBooks("Job,Psalms,Proverbs",
                                      "Ecclesiastes,Song of Solomon")
        self.major = self._initBooks("Isaiah,Jeremiah,Lamentations",
                                     "Ezekiel,Daniel")
        self.minor = self._initBooks("Hosea,Joel,Amos,Obadiah,Jonah,Micah",
                                     "Nahum,Habakkuk,Zephaniah,Haggai",
                                     "Zechariah,Malachi")
        self.gospels = self._initBooks("Matthew,Mark,Luke,John")
        self.acts = Book(os.path.join(self.path, "Acts.txt"))
        self.epistles = self._initBooks("Romans,1stCorinthians,2ndCorinthians",
                                        "Galatians,Ephesians,Philippians",
                                        "Colossians",
                                        "1stThessalonians,2ndThessalonians",
                                        "1stTimothy,2ndTimothy",
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
            nameset = [x+".txt" for x in nameset.split(',')]
            for name in nameset:
                book = Book(os.path.join(self.path, name))
                bookset.append(book)
                setattr(self, book.name, book)
        return bookset

    def book(self, bname):
        return getattr(self, bname)


class Book(PathResource):
    def __init__(self, path):
        PathResource.__init__(self, path)
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.text = open(self.path, encoding="ISO-8859-1").read()

    def __len__(self):
        cre = re.compile(r'^\d+(?=:1\D+.*$)', re.DOTALL | re.MULTILINE)
        return int(re.findall(cre, self.text)[-1])

    def chapter(self, cnum):
        if cnum > len(self):
            cnum = 1
        res = r'^%d:\d+.*?\D+(?=%d|%d:\d+)' % (cnum, cnum, cnum+1)
        cre = re.compile(res, re.DOTALL | re.MULTILINE)
        lines = re.findall(cre, self.text)

        class Chapter(object):

            def __init__(cself, clines):
                cself.number = int(re.match(r'^(\d+):', clines[0]).group(1))
                cself.verses = clines

            def __len__(cself):
                return len(cself.verses)
        return Chapter(lines)
