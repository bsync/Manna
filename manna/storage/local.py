import re, ffmpeg
from watchdog.observers import Observer
from watchdog.events import RegexMatchingEventHandler
from datetime import datetime, timedelta
from pathlib import Path
from itertools import chain
from glob import glob
from urllib.parse import quote as urlquote


class Mannager(RegexMatchingEventHandler):
    def __init__(self, rootdir):
        self.rootdir = rootdir
        super().__init__(f".+/.+", ignore_directories=True)
        self.observer = Observer()
        self.observer.schedule(self, f"{self.rootdir}", recursive=True)
        self.observer.start()
        self.series = {}
        for sdir in glob(f"{self.rootdir}/*"):
            if Path(sdir).is_dir():
                ser = Series(sdir)
                self.series[ser.name]=ser
                print(f"Created series for {sdir}... ")
        #self.series = { s.name:s for s in [ Series(y) for y in glob(f"{self.rootdir}/*") if Path(y).is_dir() ] }
        self.token = 0 #Not really needed for local

    @property
    def videos(self):
        videos = list(chain(*[ s.videos() for s in self.series.values() ]))
        return sorted(videos, key=lambda v: v.mtime)

    @property
    def videos_by_id(self):
        return { v.rid:v for v in self.videos }

    def recent_videos(self, cnt):
        return self.videos[-cnt:]

    def catalog(self, **kwargs):
        return self.series.values()

    def series_by_name(self, name):
        return self.series[name]

    def video_by_id(self, idn):
        return self.videos_by_id[idn]

    def video_for(self, sname, vname):
        return self.series_by_name(sname).video_by_name(vname)

    def on_created(self, event):
        print(f"Created {event}")

    def on_modified(self, event):
        print(f"Modified {event}")


class Record:
    def __init__(self, pathstr):
        self.rid = id(self)
        self.path = Path(pathstr)
        self.encoded_path = urlquote(str(self.path))
        self.parent = self.path.parent
        self.root, self.relative_path = Path(*self.path.parts[:2]), Path(*self.path.parts[2:])
        self.relative_stem = self.relative_path.parent.joinpath(self.relative_path.stem)
        self.relative_url = urlquote(str(self.relative_stem))
        self.stat = self.path.stat()
        self.name = self.path.stem
        self.mtime = self.stat.st_mtime
        self.date = datetime.fromtimestamp(self.mtime)


class Series(Record):
    def __init__(self, pathstr):
        super().__init__(pathstr)
        self._videos = []
        for path in glob(f"{self.path}/*.mp4"):
            try:
                self._videos.append(Video(path))
            except Exception as ex:
                print(f"Unable to parse video file at {path}, skipping it...")
        self._videos.sort(key=lambda v: v.mtime)
        self.author = "TBD"

    @property
    def video_count(self):
        return len(self._videos)

    @property
    def highest_numbered_title(self):
        if len(self._videos) > 0: 
            vid_names_str=' '.join([ vid.name for vid in self._videos ])
            vid_num_strs=re.findall('\d+', vid_names_str)
            vid_num_strs.sort(key=int)
            vid_nums = [ int(v) for v in vid_num_strs ]
            if len(vid_nums) > 0:
                return vid_nums[-1]
        return 0

    @property
    def normalizable_vids(self):
        llen = len(str(self.highest_numbered_title))
        def abnormal(vid):
            spaceout = " ".join(vid.name.split())
            spaceout = ''.join(re.split(r'(\d+)', spaceout)[0:2])
            spaceout = re.sub(r'(.*\S+)#', '\\1 #', spaceout) 
            try:
                name, digits, _ =  re.split(r'(\d+).*', vid.name)
            except ValueError as ve:
                digits='0'
            return len(digits) != llen or spaceout != vid.name
        return list(filter(abnormal, self._videos))
    
    def videos(self, **kwargs):
        if len(kwargs): #kwargs can be used to return sorted or paged sets of videos
            #The kwargs are exactly those used by DataTables for server side processing
            #see https://datatables.net/manual/server-side for details
            sortcol=kwargs['order[0][column]']  #The column number to sort by
            sortby=kwargs[f"columns[{sortcol}][data]"] #that column's associated data type
            sortdir=kwargs['order[0][dir]'] #the sort direction, 'asc' or 'desc'
            if not hasattr(self, '_currentsort') or self._currentsort != (sortby,sortdir):
                self._videos.sort(key=lambda x: getattr(x, sortby), reverse=sortdir == 'asc')
                self._currentsort = (sortby,sortdir)
            #The page start and stop indices
            start = int(kwargs['start'])
            stop = start + int(kwargs['length'])
            vids = self._videos[start:stop]
            class RecordList(list):
                def __init__(rself, lst):
                    super().__init__(lst)
                    rself.available = len(self._videos)
            return RecordList(vids)
        else:
            return self._videos

    def video_by_name(self, vname):
        return { v.name:v for v in self._videos }[vname]

    def normalized_name(self, name='', inc=0):
        if not name and len(self._videos):
            name = self._videos[-1].name
        if re.match(r'\D*\d+', name):
            name, digits, _ =  re.split(r'(\d+).*', " ".join(name.split()))
            name = re.sub(r'(.*\S+)#', '\\1 #', name) 
            digits = str(int(digits) + inc)
            dcnt = len(str(self.highest_numbered_title))
            return f"{name}{digits.zfill(dcnt)}"
        else:
            return name

    def next_vidnames(self, n):
        hnum = self.highest_numbered_title
        lvidname = self._videos[0].name if len(self._videos) else "Video #0"
        nvidnames = []
        for x in range(n):
            nvidname = re.sub(
                r"(.*\D+)(\d+)(.*)",  
                lambda s: s.group(1) + str(hnum + x + 1) + s.group(3),  
                lvidname) 
            nvidnames.append(nvidname)
            lvidname = nvidname
        return nvidnames


class Video(Record):
    def __init__(self, pathstr):
        super().__init__(pathstr)
        self.encoded_audio_path = urlquote(str(self.audio_file))

    def __getattr__(self, k):
        if k == '_meta':
            raise AttributeError()
        elif not hasattr(self, '_meta'):
            print(f"Probing {self.path}")
            try:
                self._meta = ffmpeg.probe(self.path)
                fmeta = self._meta.get('format', {})
                vmeta, ameta = self._meta.get('streams', [{}, {}]) 
            except Exception as ex:
                print(f"Bad mojo parsing {self.path}; defaulting.")
                self._meta = fmeta = vmeta = ameta = {}
            self.duration = timedelta(seconds=round(float(fmeta.get('duration', 0.0))))
            self.width = vmeta.get('width', 0)
            self.height = vmeta.get('height', 0)
            return getattr(self, k)
        else:
            raise AttributeError()

    @property
    def audio_file(self):
        return self.path.with_suffix('.mp3')

    @property
    def audio_stream(self):
        if not self.audio_file.exists():
            self.generate_audio_file()
        def stream_audio():
            with open(self.audio_file, 'rb') as afile:
                chk = afile.read(1000)
                while chk != b"":
                    yield chk
                    chk = afile.read(1000)
        return stream_audio()

    def generate_audio_file(self):
        stream = ffmpeg.input(self.path)
        agproc = ffmpeg.output(stream, filename=self.audio_file, ac=1, ab="64k", ar=44100)
        agproc.run_async()

