import os, sys, vimeo, json, datetime, re, math


class VimeoClient(vimeo.VimeoClient):
    def __init__(self):
        super().__init__(os.getenv('VIMEO_TOKEN'),
                         os.getenv('VIMEO_CLIENT_ID'),
                         os.getenv('VIMEO_CLIENT_SECRET'))
        self._cache = {}

    @property
    def catalog(self):
        return self.cache('catalog', Series, sort="date", direction="desc")

    def cache(self, key, record, **kwargs):
        if key not in self._cache:
            self._cache[key] = self.collect(record, **kwargs)
        return self._cache[key] 

    def purge_cache(self, *cache_items):
        for cache_item in cache_items:
            for cache_key in cache_item.cache_keys:
                if cache_key in self._cache:
                    del self._cache[cache_key]

    def latest_videos(self, cnt):
        return self.collect(Video,
                    sort="date", 
                    direction="desc", 
                    length=cnt,
                    filter_fn=lambda x: x.parent_folder != None)

    def series_by_name(self, name):
        return self.cache(name, Series, query=name)[0]

    def add_new_series(self, aname, adescription="TODO: Describe me"):
        self.post(Series.URI, data=dict(name=aname, description=adescription))
        return self.series_by_name(aname)

    def add_videos_to_series(self, series, *vid_ids):
        vuris = ','.join([f"/videos/{vid}" for vid in vid_ids ])
        query = f"{series.uri}/videos?uris={vuris}"
        self.purge_cache(series)
        return self.put(query)

    def purge_video_from_series(self, series, vidname):
        video = series.video_by_name(vidname)
        return self.delete(f"{series.uri}/videos/{video.id}")

    def collect(qself, cls, uri=None, filter_fn=lambda x: True, **qparams):
        length = int(qparams.get('length', 0))
        fetched_records = []
        uri = cls.URI if uri is None else uri
        qparams.update(fields=cls.FIELDS, **qparams)
        if 'start' in qparams:
            pagelen = int(qparams.get('length', 10))
            pagenum = math.ceil((int(qparams['start']) + 1) / pagelen)
            qparams.update(page=pagenum, per_page=pagelen)
        sinfo = qself.get(uri, params=qparams).json()
        while('data' in sinfo):
            for vsinfo in sinfo['data']: 
                vsobj = cls(qself, vsinfo)
                if filter_fn(vsobj):
                    fetched_records.append(vsobj)
                if length > 0 and length <= len(fetched_records): 
                    return fetched_records
            nextpage = sinfo.get('paging', {}).get('next', False)
            if nextpage:
                sinfo = qself.get(nextpage).json()
            else:
                sinfo = {}
        return fetched_records


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
          +"created_time,duration," \
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
    def parent_series_name(self):
        ps = self.parent_series
        return ps.name if ps else "Not part of a series"

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
        self.source.purge_cache(self.parent_series)
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
        self.source.purge_cache(self)
        return resp


class Series(Record):
    URI='/me/projects'
    FIELDS="uri,name,embed,files,download," \
          +"created_time,duration," \
          +"pictures.sizes.link," \
          +"metadata.connections.items.total"

    @property
    def cache_keys(self):
        return f"catalog {self.name} {self.name}_videos".split()

    @property
    def video_count(self):
        return int(self.metadata['connections']['items']['total'])

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

    def videos(self, **kwargs):
        #return self.source.cache(f"{self.name}_videos", 
        return self.source.collect(Video, uri=f"{self.uri}/videos", **kwargs)

    def video_by_name(self, name):
        return self.videos(query=name)[0]

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
