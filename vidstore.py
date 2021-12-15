import os, sys, vimeo, json, datetime, re, math


class VimeoClient(vimeo.VimeoClient):
    def __init__(self):
        super().__init__(os.getenv('VIMEO_TOKEN'),
                         os.getenv('VIMEO_CLIENT_ID'),
                         os.getenv('VIMEO_CLIENT_SECRET'))
        self._cache = {}

    def catalog(self, **kwargs):
        kwargs.setdefault('sort', 'modified_time')
        kwargs.setdefault('direction', 'desc')
        return self.collect(Series, **kwargs)

    def latest_videos(self, cnt):
        return self.collect(Video, sort="date", direction="desc", length=cnt)

    def _filter_vid(self, vid):
        return vid.parent_folder != None

    def series_by_name(self, name):
        return self.collect(Series, query=name)[0]

    def add_new_series(self, aname, adescription="TODO: Describe me"):
        self.post(Series.URI, data=dict(name=aname, description=adescription))
        return self.series_by_name(aname)

    def add_videos_to_series(self, series, *vid_ids):
        vuris = ','.join([f"/videos/{vid}" for vid in vid_ids ])
        query = f"{series.uri}/videos?uris={vuris}"
        return self.put(query)

    def purge_video_from_series(self, series, vidname):
        video = series.video_by_name(vidname)
        return self.delete(f"{series.uri}/videos/{video.id}")

    def collect(qself, cls, uri=None, **qparams):
        uri = cls.URI if uri is None else uri
        length = int(qparams.get('length', 10))
        cparams = dict(
            per_page=length,
            page=math.ceil((int(qparams.pop('start', 0))+1)/length),
            fields=cls.FIELDS,
            sort=qparams.pop('sort', 'date'),
            direction=qparams.pop('direction', 'desc'),
	    query=qparams.get('query', ''))
        sinfo = qself.get(uri, params=cparams).json()
        record_list = RecordList(int(sinfo.get('total', 0)))
        while('data' in sinfo):
            for vsinfo in sinfo['data']: 
               record_list.append(cls(qself, vsinfo))
            if 'length' not in qparams:
                nextpage = sinfo.get('paging', {}).get('next', False)
                if nextpage:
                    sinfo = qself.get(nextpage).json()
                else:
                    sinfo = {}
            else:
                sinfo = {}
        return record_list

        #start = int(qparams.pop('start', 0))
        #length = int(qparams.pop('length', 10))
        ##qparams.setdefault('per_page', math.ceil((int(qparams['start']) + 1) / page))
        #qparams.update(fields=cls.FIELDS)
        #qparams['page'] = str(start)
        #qparams['per_page'] = str(length)
        #sinfo = qself.get(uri, params=qparams).json()
        #record_list = RecordList(int(sinfo.get('total', 0)))
        #while('data' in sinfo):
        #    for vsinfo in sinfo['data']: 
        #        vsobj = cls(qself, vsinfo)
        #        if filter_fn(vsobj):
        #            record_list.append(vsobj)
        #        if length > 0 and length <= len(record_list): 
        #            return record_list
        #    nextpage = sinfo.get('paging', {}).get('next', False)
        #    if nextpage:
        #        sinfo = qself.get(nextpage).json()
        #    else:
        #        sinfo = {}
        #return record_list

class RecordList(list):
    def __init__(self, avail):
        self.available = avail

class Record(dict):
    def __init__(self, source, info):
        super().__init__(info)
        self.source = source

    @property
    def cache_keys(self):
        return []

    @property
    def date(self):
        try:
            dt = datetime.datetime.fromisoformat(json.loads(self.description)['date'])
            dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt
        except:
            return self.created_date

    @property
    def created_date(self):
        dt = datetime.datetime.fromisoformat(self.created_time)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt

    @property
    def id(self):
        return self.uri.rpartition('/')[2]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"Invalid attribute {name}")


class Video(Record):
    URI='/me/videos'
    FIELDS="uri,link,name,description,embed,files,download," \
          +"created_time,duration,last_user_action_event_date," \
          +"height,width," \
          +"pictures.sizes.link," \
          +"parent_folder.name"

    @property
    def parent_series(self):
        if self.parent_folder is None:
            return None
        sname = self.parent_folder['name']
        return {s.name:s for s in self.source.catalog}[sname]

    @property 
    def parent_name(self):
        pn = self.parent_folder['name']
        return pn if pn else "Not part of a series"

    @property
    def html(self):
        return self.embed['html']

    @property
    def downlink(self):
        return self.download[0]['link']

    @property
    def plink(self):
        return self.pictures['sizes'][0]['link']

    @property
    def vlink(self):
        return self.files[0]['link']

    @property
    def quality(self):
        return self.files[0]['quality']

    @property
    def duration(self):
        return str(datetime.timedelta(seconds=int(self['duration'])))

    def nth_next_name(self, n):
        """ Match one or more digits in the middle of the video's current name
            and replace it with value of the digits incremented by one
        """
        return re.sub(
                r"(.*\D+)(\d+)(.*)",  
                lambda x: x.group(1) + str(int(x.group(2)) + n) + x.group(3),  
                self.name) 

    def save(self, **kwargs):
        resp = self.source.patch(self.uri, data=kwargs)
        return resp

    def redate(self, newdt):
        try:
            jdesc = json.loads(self.description)
        except:
            jdesc = {}
        if isinstance(newdt, str):
            newdt = datetime.datetime.strptime(newdt, "%Y-%m-%d")
        jdesc['date'] = str(newdt.date())
        resp = self.source.patch(
                    f"{self.uri}", 
                    data=dict(description=json.dumps(jdesc)))
        return resp


class Series(Record):
    URI='/me/projects'
    FIELDS="uri,name,embed,files,download," \
          +"created_time,modified_time,duration," \
          +"pictures.sizes.link," \
          +"metadata.connections.items.total"

    @property
    def cache_keys(self):
        return f"catalog {self.name} {self.name}_videos".split()

    @property
    def video_count(self):
        return int(self.metadata['connections']['items']['total'])

    @property
    def date(self):
        dt = datetime.datetime.fromisoformat(self.modified_time)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt

    @property
    def highest_numbered_title(self):
        vids = self.videos()
        if len(vids) > 0: 
            vid_names_str=' '.join([ vid.name for vid in vids ])
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
        return list(filter(abnormal, self.videos()))

    def purge_video(self, vidname):
        return self.source.purge_video_from_series(self, vidname)

    def nth_next_vidname(self, n):
        svids = sorted(self.videos(), key=lambda v : v['created_time'])
        return svids[-1].nth_next_name(n) if self.video_count else "Lesson #1"

    def add_videos(self, *vid_ids):
        #Send all vid.uri's to vimeo at once to have it associate all with this folder/series
        return self.source.add_videos_to_series(self, *vid_ids)

    def video_by_name(self, name):
        return { v.name:v for v in self.videos() }[name]

    def videos(self, **kwargs):
        return self.source.collect(Video, uri=f"{self.uri}/videos", **kwargs)

    def normalized_name(self, name='', inc=0):
        vids = self.videos()
        if not name and len(vids):
            name = vids[-1].name
        if re.match(r'\D*\d+', name):
            name, digits, _ =  re.split(r'(\d+).*', " ".join(name.split()))
            name = re.sub(r'(.*\S+)#', '\\1 #', name) 
            digits = str(int(digits) + inc)
            dcnt = len(str(self.highest_numbered_title))
            return f"{name}{digits.zfill(dcnt)}"
        else:
            return name


class MannaStore:
    def __new__(self):
        return VimeoClient()
