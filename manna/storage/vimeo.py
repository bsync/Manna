import vimeo, json, datetime, re, math, os, subprocess 

class VimeoMannager(vimeo.VimeoClient):

    def __init__(self, app):
        super().__init__(app.config['VIMEO_TOKEN'], app.config['VIMEO_CLIENT_ID'], app.config['VIMEO_CLIENT_SECRET'])
        self.latest_cnt = app.config.get('LATEST_CNT', 10)
        recentsc = app.config.get("RECENTS", "Recent")
        self.recents = self.showcase_by_name(recentsc, makeit=True)
        rvids = self.recents.videos()
        vidcnt = len(rvids)
        if vidcnt < self.latest_cnt:
            vids = self.collect(Video, sort="date", direction="desc", length=self.latest_cnt)
            for vid in vids:
                if vid not in rvids:
                    self.recents.add_videos(vid.id)
        elif vidcnt > self.latest_cnt:
            for vid in rvids[self.latest_cnt:]:
                self.recents.purge(vid)

    @property
    def recent_videos(self):
        return self.recents.videos()

    @property
    def latest_videos(self):
        return self.collect(Video, sort="date", direction="desc", length=self.latest_cnt)

    def catalog(self, **kwargs):
        return self.collect(Series, **kwargs)

    def showcase_by_name(self, name, makeit=False):
        slist = self.collect(Showcase, query=name)
        if len(slist) < 1:
            if makeit:
                return self.add_new_series(recentsc, cls=Showcase)
            else:
                raise NoSuchResource(f"No Showcase matching: {name}")
        return slist[0]

    def series_by_id(self, id):
        return self.collect(Series, f"{Series.URI}/{id}")[0]

    def series_by_name(self, name):
        slist = self.collect(Series, query=name)
        if len(slist) < 1:
            raise NoSuchResource(f"No Series matching: {name}")
        return slist[0]

    def video_by_id(self, id):
        vid = self.collect(Video, f"{Video.URI}/{id}")[0]
        return vid

    def audio_by_id(self, id):
        vid = self.video_by_id(id)
        ffin = f' -i "{vid.vlink}" '
        ffopts = "-ac 1 -ab 64k -ar 44100 -f mp3 "
        ffout = ' - '
        ffmpeg = 'ffmpeg' + ffin + ffopts + ffout
        tffmpeg = "timeout -s SIGKILL 300 " + ffmpeg 
        def generate_mp3():
            with subprocess.Popen(tffmpeg, shell=True,
                          stdout = subprocess.PIPE, stderr=subprocess.PIPE,
                          close_fds = True, preexec_fn=os.setsid) as process:
                while process.poll() is None:
                    yield process.stdout.read(1000)
        return generate_mp3()


    def _filter_vid(self, vid):
        return vid.parent_folder != None

    def add_new_series(self, aname, adescription="TODO: Describe me", cls=None):
        cls = cls if cls else Series
        self.post(cls.URI, data=dict(name=aname, description=adescription))
        return self.series_by_name(aname)

    def add_videos_to_showcase(self, showcase, *vid_ids):
        for vidid in vid_ids:
            self.put(f"{showcase.uri}/videos/{vidid}")

    def add_videos_to_series(self, series, *vid_ids):
        vuris = ','.join([f"/videos/{vid}" for vid in vid_ids ])
        query = f"{series.uri}/videos?uris={vuris}"
        return self.put(query)

    def purge_video_from_series(self, series, vid):
        if type(vid) == str:
            vid = series.video_by_name(vid)
        return self.delete(f"{series.uri}/videos/{vid.id}")

    def adjust_recents(self, video):
        adjusted = False
        rvids = self.recents.videos()
        if video.id not in [ r.id for r in rvids ]:
            if len(rvids) < self.latest_cnt:
                self.recents.add_videos(video.id)
                adjusted = True
            elif video.date >= self.recents.oldest.date:
                self.recents.add_videos(video.id)
                adjusted = True
        vids = self.recents.videos()
        while len(vids) > self.latest_cnt:
            self.recents.purge(vids[-1])
            vids = vids[:-1]
            adjusted = True
        return adjusted

    def collect(self, cls, uri=None, **params):
        uri = cls.URI if uri is None else uri
        length = int(params.get('length', 10))
        vimeo_params = dict(
            per_page=length,
            page=math.ceil((int(params.get('start', 0))+1)/length),
            fields=cls.FIELDS,
            sort=params.get(f"columns[{params.get('order[0][column]', 0)}][data]", 'date'),
            direction=params.get('direction', params.get('order[0][dir]', 'desc'))) #table's sort direction
        if 'query' in params:
            vimeo_params.update(query=params['query'])
        elif 'search[value]' in params:
            vimeo_params.update(query=params['search[value]'])
        sinfo = self.get(uri, params=vimeo_params).json() # VimeoClient fetch happens here
        record_list = RecordList(int(sinfo.get('total', 0)))
        if('data' not in sinfo):
            record_list.append(cls(self, sinfo))
        else:
            while('data' in sinfo):
                for vsinfo in sinfo['data']: 
                   record_list.append(cls(self, vsinfo))
                if 'length' in params:
                    sinfo = {}
                else:
                    nextpage = sinfo.get('paging', {}).get('next', False)
                    if nextpage:
                        sinfo = self.get(nextpage).json()
                    else:
                        sinfo = {}
        return record_list


class RecordList(list):
    def __init__(self, avail):
        self.available = avail

    def __sub__(self, other):
        oids = [ x.id for x in other ]
        return [ x for x in self if x.id not in oids ]


#Define manna record components:

class Record(dict):
    def __init__(self, source, info):
        super().__init__(info)
        self.source = source
        self.id = self.uri.rpartition('/')[2]

    @property
    def date(self):
        try:
            dt = datetime.datetime.fromisoformat(json.loads(self['description'])['date'])
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
    def author(self):
       return "Pastor Ward"

    @property
    def description(self):
        try:
            jload = json.loads(self['description'])
            return jload.get('description', "No description!")
        except:
            return self['description']

    def __hash__(self):
        return self.id

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
    def described(self):
        if self.description:
            return f"{self.name} : {self.description}"
        else:
            return f"{self.name}"

    @property
    def parent_series(self):
        if self.parent_folder is None:
            return None
        sname = self.parent_folder['name']
        return self.source.series_by_name(sname)

    @property 
    def parent_name(self):
        try:
            return self.parent_folder['name']
        except:
            return "Not part of a series"

    @property
    def html(self):
        return self.embed['html']

    @property
    def downlink(self):
        return self.download[0]['link']

    @property
    def plink(self):
        return self.pictures['sizes'][-1]['link']

    @property
    def vlink(self):
        return self.files[0]['link']

    @property
    def quality(self):
        return self.files[0]['quality']

    @property
    def duration(self):
        return datetime.timedelta(seconds=int(self['duration']))

    def save(self, **kwargs):
        resp = self.source.patch(self.uri, data=kwargs)
        return resp

    def redate(self, newdt):
        try:
            jdesc = json.loads(self['description'])
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
          +"metadata.connections.videos.total"

    @property
    def video_count(self):
        return int(self.metadata['connections']['videos']['total'])

    @property
    def date(self):
        dt = datetime.datetime.fromisoformat(self.modified_time)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt

    @property
    def newest(self):
        return self.videos()[0]

    @property
    def oldest(self):
        return self.videos()[-1]

    @property
    def highest_numbered_title(self):
        vids = self.videos(direction="desc", length=10)
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

    def purge(self, video):
        return self.source.purge_video_from_series(self, video)

    def purge_video(self, vidname):
        return self.source.purge_video_from_series(self, vidname)

    def next_vidnames(self, n):
        svids = self.videos(direction="desc", length=10)
        lvidname = svids[0].name if len(svids) else "Video #0"
        nvidnames = []
        for x in range(n):
            nvidname = re.sub(
                r"(.*\D+)(\d+)(.*)",  
                lambda x: x.group(1) + str(int(x.group(2)) + 1) + x.group(3),  
                lvidname) 
            nvidnames.append(nvidname)
            lvidname = nvidname
        return nvidnames

    def add_videos(self, *vid_ids):
        #Send all vid.uri's to vimeo at once to have it associate all with this folder/series
        return self.source.add_videos_to_series(self, *vid_ids)

    def video_by_name(self, name):
        try:
            return self.videos(query=name)[0]
        except IndexError:
            raise Exception(f"Unable to access video named {name} from series {self.name}")
        #return { v.name:v for v in self.videos() }[name]

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

    def __contains__(self, record):
        return record.id in [ x.id for x in self.videos() ]


class Showcase(Series):
    URI='/me/albums'

    def add_videos(self, *vid_ids):
        #Send all vid.uri's to vimeo at once to have it associate all with this folder/series
        return self.source.add_videos_to_showcase(self, *vid_ids)


class NoSuchResource(Exception):
    pass


