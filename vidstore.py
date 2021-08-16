import os, sys, vimeo, json, datetime, re, math
import requests_cache
requests_cache.install_cache('vidstore_cache')
requests_cache.clear()
rcache = requests_cache.get_cache()


class VimeoClient(vimeo.VimeoClient):
    def __init__(self, app):
        super().__init__(os.getenv('VIMEO_TOKEN'),
                         os.getenv('VIMEO_CLIENT_ID'),
                         os.getenv('VIMEO_CLIENT_SECRET'))
        self.vQuery = Query(self, Video, sort="date", direction="desc") 

    @property
    def catalog(self):
        return Query(self, Series, sort="date", direction="desc")()

    def series_by_name(self, name):
        return Query(self, Series, query=name)()[0]

    def latest_videos(self, cnt):
        self.vQuery.filters_out(parent_folder=None)
        return self.vQuery(length=cnt)

    def add_new_series(self, aname, adescription="TODO: Describe me"):
        self.post(Series.URI, data=dict(name=aname, description=adescription))
        return self.series_by_name(aname)

    def clear_cache(self, url=None, url_frag=None):
        if url:
            rcache.delete_url(url)
        elif url_frag:
            for murl in rcache.urls:
                if url_frag in murl:
                    rcache.delete_url(murl)
        else:
            requests_cache.clear()


class Record(dict):
    def __init__(self, source, info):
        super().__init__(info)
        self.source = source

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

    @property
    def next_name(self):
        """ Match one or more digits in the middle of the video's current name
            and replace it with value of the digits incremented by one
        """
        return re.sub(
                r"(.*\D+)(\d+)(.*)",  
                lambda x: x.group(1) + str(int(x.group(2)) + 1) + x.group(3),  
                self.name) 

    def save(self, **kwargs):
        self.source.patch(self.uri, data=kwargs)

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
        self.source.clear_cache(url_frag=self.parent_series.uri)
        return resp

    def purge(self):
        resp = self.source.delete(f"{self.uri}")
        self.source.clear_cache(url_frag=self.parent_series.uri)
        return resp

class Series(Record):
    URI='/me/projects'
    FIELDS="uri,name,embed,files,download," \
          +"created_time,duration," \
          +"pictures.sizes.link," \
          +"metadata.connections.items.total"

    @property
    def video_count(self):
        return int(self.metadata['connections']['items']['total'])

    @property
    def next_vid_name(self):
        svids = sorted(self.videos(), key=lambda v : v['name'])
        return svids[-1].next_name if self.video_count else "Lesson #1"

    def add_videos(self, *vid_ids):
        #Send all vid.uri's to vimeo at once to have it associate all with this folder/series
        vuris = ','.join([f"/videos/{vid}" for vid in vid_ids ])
        query = f"{self.uri}/videos?uris={vuris}"
        return self.source.put(query)

    def videos(self, **kwargs):
        return self.source.vQuery(f"{self.uri}/videos", **kwargs)

    def video_by_name(self, name):
        return { v.name:v for v in self.videos() }[name]


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


class Query(dict):
    db = None
    def __init__(qself, db, cls, **kwargs):
        super().__init__(**kwargs)
        qself.db = db
        qself.cls = cls
        qself.length = kwargs.pop('length', None)
        qself.filterArgs = {}

    def filters_out(qself, subject=None, **kwargs):
        qself.filterArgs.update(**kwargs)
        if subject:
            for k,v in qself.filterArgs.items():
                if k in subject and subject[k] == v:
                    return True
            return False
        return True

    def __call__(qself, uri=None, **kwargs):
        length = int(kwargs.get('length', 0))
        fetched_records = []
        uri = qself.cls.URI if uri is None else uri
        qparams = dict(qself)
        qparams.update(fields=qself.cls.FIELDS, **kwargs)
        if 'start' in qparams:
            pagelen = int(kwargs.get('length', 10))
            pagenum = math.ceil((int(kwargs['start']) + 1) / pagelen)
            qparams.update(page=pagenum, per_page=pagelen)
        sinfo = qself.db.get(uri, params=qparams).json()
        while('data' in sinfo):
            for vsinfo in sinfo['data']: 
                vsobj = qself.cls(qself.db, vsinfo)
                if not qself.filters_out(vsobj): 
                    fetched_records.append(vsobj)
                if length > 0 and length <= len(fetched_records): 
                    return fetched_records
            nextpage = sinfo.get('paging', {}).get('next', False)
            if nextpage:
                sinfo = qself.db.get(nextpage).json()
            else:
                sinfo = {}
        return fetched_records


class MannaStore:
    def __new__(self, app):
        return VimeoClient(app)
