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

def init_app(app):
    db.init_app(app)
    db.status = "ready"


class VimeoRecord(db.Document):
    meta = {'allow_inheritance': True}
    uri = db.StringField(required=True, primary_key=True)
    name = db.StringField(required=True)
    description = db.StringField()
    html = db.StringField()
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

    @classmethod
    def create_or_update(cls, vinfo):
        vid = cls.objects(uri=vinfo['uri']).first()
        if vid: 
            vid.name = vinfo['name']
            vid.html = vinfo['embed']['html']
        else:
            vid = Video(uri=vinfo['uri'], 
                        name=vinfo['name'],
                        html=vinfo['embed']['html'],
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
                              html=ainfo['embed']['html'],
                              create_date=ainfo['created_time'],)
            alb._sync_vids()
        return alb

    @classmethod
    def named(cls, aname):
        return cls.objects(name=aname).first()

    @classmethod
    def add_new(cls, aname, adescription):
        if VideoSeries.objects(name=aname).count() > 0: 
            raise Exception(f"VideoSeries {aname} already exists.")
        resp = vcpost('/me/albums', name=aname, description=adescription).json()
        resp2 = vcpost('/me/projects', name=aname).json()
        alb = VideoSeries(uri=resp['uri'], 
                          name=resp['name'],
                          html=resp['embed']['html'],
                          create_date=resp['created_time'],)
        alb.save()
        return alb

    def upload_action(self, vid_name, vid_desc, redir="/"):
        vp = vcpost("/me/videos", 
                    **dict(name=vid_name,
                           description=vid_desc,
                           upload=dict(approach="post", redirect_url=redir)))
        vp = vp.json()
        return vp['upload']['upload_link']

    def add_video(self, viduri):
        resp = vcput(f"{self.id}{viduri}")
        if resp.ok:
            resp = vcget(viduri)
            while resp.json()['status'] != 'available':
                time.sleep(3)
                resp = vcget(viduri)
        self.synchronize()
        return Video.objects(uri=viduri).first()

    def get_video_named(self, vname):
        return { x.name:x for x in self.videos }[vname]

    def remove(self):
        vimeourl = self.uri
        self.delete()
        vcdel(vimeourl) 

    @classmethod
    def sync_all(cls):
        db.status = statstr = "Syncronizing "
        lainfo = vcget('/me/albums', 
                       fields="uri,name,embed,created_time",
                       sort="date",
                       direction="desc").json()
        while('data' in lainfo):
            for ainfo in lainfo['data']: 
                try:
                   db.status = statstr + VideoSeries.create_or_update(ainfo).name
                except db.ValidationError as mve:
                   print(f"Skipping import of {ainfo['name']} due to {mve}")
            nextpage = lainfo.get('paging', {}).get('next', False)
            if nextpage:
                lainfo = vcget(nextpage).json()
            else:
                lainfo = {}
        db.status = "ready"

    def synchronize(self):
        ainfo = vcget(self.uri,
                      fields="uri,name,embed,created_time",
                      sort="date",
                      direction="desc").json()
        self.name=ainfo['name']
        self.html=ainfo['embed']['html']
        self._sync_vids()
        return self

    def _sync_vids(self):
        if db.status == "ready":
            db.status = f"Synchronizing {self.name}..."
        vlinfo = vcget(f"{self.uri}/videos",
                       fields="uri,name,embed,created_time,duration,"
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
        db.status = "ready"

def _drop_all():
    VideoSeries.drop_collection()
    Video.drop_collection()
    VimeoRecord.drop_collection()

