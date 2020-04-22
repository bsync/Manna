import os, time, datetime as dt, vimeo, flask
from flask_mongoengine import MongoEngine

vc = vimeo.VimeoClient(os.getenv('VIMEO_TOKEN'),
                       os.getenv('VIMEO_CLIENT_ID'),
                       os.getenv('VIMEO_CLIENT_SECRET'))

def vcget(url, **kwargs):
    return check_response(vc.get(url, params=kwargs))

def vcpost(url, **kwargs):
    return check_response(vc.post(url, data=kwargs))

def vcput(url, **kwargs):
    return check_response(vc.put(url, data=kwargs))

def vcdel(url, **kwargs):
    return check_response(vc.delete(url, params=kwargs))

def check_response(resp):
    class VimeoException(Exception):
        pass
    if resp.status_code > 399:
        raise VimeoException(f"Vimeo Response: {resp.json()}")
    return resp

db = MongoEngine()

def init_flask(app):
    db.init_app(app)

def sync_series(sname=None):
    yield "Syncronizing "
    lainfo = vcget('/me/projects', 
                   fields="uri,name,created_time",
                   sort="date",
                   direction="desc").json()
    while('data' in lainfo):
        for ainfo in lainfo['data']: 
            try:
               if ainfo['name'] == sname or sname is None:
                   yield "Synchronizing " + VideoSeries.create_or_update(ainfo).name
            except db.ValidationError as mve:
               print(f"Skipping import of {ainfo['name']} due to {mve}")
        nextpage = lainfo.get('paging', {}).get('next', False)
        if nextpage:
            lainfo = vcget(nextpage).json()
        else:
            lainfo = {}
    yield "ready"


class VimeoRecord(db.Document):
    meta = {'allow_inheritance': True}
    uri = db.StringField(required=True, primary_key=True)
    name = db.StringField(required=True)
    description = db.StringField()
    create_date = db.DateField(required=True, default=dt.datetime.utcnow)

    @property
    def vimid(self):
        return int(self.uri.rpartition('/')[2])

    @classmethod
    def latest(cls, cnt):
        return cls.objects().order_by('-create_date')[:cnt]


class Video(VimeoRecord):
    album = db.ReferenceField('VideoSeries')
    duration = db.IntField(required=True)
    html = db.StringField()
    vlink = db.StringField(required=True)
    dlink = db.StringField(required=True)

    @classmethod
    def create_or_update(cls, vinfo):
        vid = cls.objects(uri=vinfo['uri']).first()
        if vid: 
            vid.name = vinfo['name']
            vid.html = vinfo['embed']['html']
            vid.vlink = vinfo['files'][0]['link']
            vid.dlink = vinfo['download'][0]['link']
        else:
            vid = Video(uri=vinfo['uri'], 
                        name=vinfo['name'],
                        html=vinfo['embed']['html'],
                        vlink=vinfo['files'][0]['link'],
                        dlink=vinfo['download'][0]['link'],
                        create_date=vinfo['created_time'],
                        duration=vinfo['duration'])
            print(f"Created new Video from vimeo source {vid.name}")
        return vid

    @classmethod 
    def matching_id(cls, vimid):
        return cls.objects(uri=f"/videos/{vimid}").first()

    @property
    def next_name(self):
        nextname = f"{self.name} #2"
        try:
            npart = self.name.partition("#")
            if npart[2]:
                pnum = int(npart[2])+1
                nextname = f"{npart[0]}{npart[1]}{pnum}"
        except:
            pass
        return nextname


class VideoSeries(VimeoRecord):
    videos = db.ListField(db.ReferenceField(Video, db.PULL))

    @classmethod
    def create_or_update(cls, ainfo):
        alb = cls.objects(uri=ainfo['uri']).first()
        if alb:
            alb = alb.synchronize()
        else:
            alb = VideoSeries(uri=ainfo['uri'], 
                              name=ainfo['name'],
                              create_date=ainfo['created_time'],)
            alb._sync_vids()
        return alb

    @classmethod
    def named(cls, aname):
        existing = cls.objects(name=aname).first()
        if not existing:
            for stat in  sync_series(aname):
                print(f"Got {stat}")
            existing = cls.objects(name=aname).first()
        return existing

    @classmethod
    def add_new(cls, aname, adescription):
        if VideoSeries.objects(name=aname).count() > 0: 
            raise Exception(f"VideoSeries {aname} already exists.")
        resp = vcpost('/me/project', name=aname, description=adescription).json()
        alb = VideoSeries(uri=resp['uri'], 
                          name=resp['name'],
                          create_date=resp['created_time'],)
        alb.save()
        return alb

    def upload_action(self, vid_name, vid_desc, redir="/"):
        yield "Waiting for upload to begin..."
        vp = vcpost("/me/videos", 
                    **dict(name=vid_name,
                           description=vid_desc,
                           upload=dict(approach="post", redirect_url=redir)))
        return vp.json()['upload']['upload_link']

    def add_video(self, viduri):
        yield "Upload complete waiting for vid to become avaialble..."
        resp = vcput(f"{self.id}{viduri}")
        if resp.ok:
            resp = vcget(viduri).json()
            secs = 0
            while  resp['status'] != 'available':
                time.sleep(5)
                secs += 5
                resp = vcget(viduri).json()
                yield f"Status after {secs} seconds: {resp['status']}"
        self.synchronize()
        yield "ready"

    def get_video_named(self, vname):
        return { x.name:x for x in self.videos }[vname]

    def remove(self):
        vimeourl = self.uri
        self.delete()
        vcdel(vimeourl) 

    def synchronize(self):
        ainfo = vcget(self.uri,
                      fields="uri,name,embed,created_time",
                      sort="date",
                      direction="desc").json()
        self.name=ainfo['name']
        self._sync_vids()
        return self

    def _sync_vids(self):
        vlinfo = vcget(f"{self.uri}/videos",
               fields="uri,name,embed,files,download,created_time,duration,"
                     +"metadata.connections.albums",
                       sort="date",
                       direction="asc").json()
        if 'data' in vlinfo: 
            self.videos.clear()
        while ('data' in vlinfo):
            for vinfo in vlinfo['data']:
                try:
                    vid = Video.create_or_update(vinfo)
                    self.videos.append(vid)
                    vid.album = self
                    vid.save()
                except db.ValidationError as mve:
                   print(f"Skipping import of {vinfo['name']} due to {mve}")
            nextpage = vlinfo.get('paging', {}).get('next', False)
            if nextpage:
                vlinfo = vcget(nextpage).json()
            else:
                vlinfo = {}
        self.save()

    def replace_videos(self, vids):
        vuri_list = ",".join([ v.uri for v in vids ])
        resp = vcput(f'/me/albums/{self.vimid}/videos', videos=vuri_list)
        #self.synchronize()
        #self.save()

def _drop_all():
    VideoSeries.drop_collection()
    Video.drop_collection()
    VimeoRecord.drop_collection()

