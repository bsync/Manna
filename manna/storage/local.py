import os, re
import mutagen
from watchdog.observers import Observer
from watchdog.events import RegexMatchingEventHandler
from datetime import datetime, timedelta
from pathlib import Path
from itertools import chain
from glob import glob


class Mannager(RegexMatchingEventHandler):
    def __init__(self, rootdir, latest_cnt):
        self.rootdir, self.latest_cnt = rootdir, latest_cnt
        super().__init__(f".+/.+", ignore_directories=True)
        self.observer = Observer()
        self.observer.schedule(self, f"{self.rootdir}", recursive=True)
        self.observer.start()
        self.series = { s.name:s for s in [ Series(y) for y in glob(f"{self.rootdir}/*") if Path(y).is_dir() ] }
        self.videos = list(chain(*[ s.videos() for s in self.series.values() ]))
        self.token = 0 #Not really needed for local

    @property
    def recent_videos(self):
        return self.videos[-self.latest_cnt:]

    def catalog(self, **kwargs):
        return self.series.values()

    def series_by_name(self, name):
        return self.series[name]

    def on_created(self, event):
        print(f"Created {event}")


class Record:
    def __init__(self, pathstr):
        self.path = Path(pathstr)
        self.stat = self.path.stat()
        self.id = self.described = self.name = self.path.stem
        self.parent_name = self.path.parent.name
        self.mtime = self.stat.st_mtime
        self.date = datetime.fromtimestamp(self.mtime)


class Series(Record):
    def __init__(self, pathstr):
        super().__init__(pathstr)
        self._videos = [ Video(x) for x in glob(f"{self.path}/*.mp4") ]
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
        return self._videos

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
        lvidname = self._videos[0].name if len(self._videos) else "Video #0"
        nvidnames = []
        for x in range(n):
            nvidname = re.sub(
                r"(.*\D+)(\d+)(.*)",  
                lambda x: x.group(1) + str(int(x.group(2)) + 1) + x.group(3),  
                lvidname) 
            nvidnames.append(nvidname)
            lvidname = nvidname
        return nvidnames


class Video(Record):
    def __init__(self, pathstr):
        super().__init__(pathstr)
        self.muta = mutagen.File(self.path)
        self.meta = self.muta.info

    @property
    def duration(self):
        return str(timedelta(seconds=round(self.meta.length)))

