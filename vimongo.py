import os, flask_mongoengine, vimeo
from datetime import datetime

status = "ready"
mdb = flask_mongoengine.MongoEngine()
vc = vimeo.VimeoClient(
        os.getenv('VIMEO_TOKEN'),
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

class VimeoRecord(mdb.Document):
    meta = {'allow_inheritance': True}
    uri = mdb.StringField(required=True, primary_key=True)
    name = mdb.StringField(required=True)
    description = mdb.StringField()
    html = mdb.StringField()
    create_date = mdb.DateField(required=True, default=datetime.utcnow)

    @property
    def vimid(self):
        return int(self.uri.rpartition('/')[2])

    @classmethod
    def latest(cls, cnt):
        return cls.objects().order_by('-create_date')[:cnt]


class Video(VimeoRecord):
    album = mdb.ReferenceField('VideoSeries')
    duration = mdb.IntField(required=True)
   
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
        npart = self.name.partition("#")
        if npart[2]:
            pnum = int(npart[2])+1
            nextname = f"{npart[0]}{npart[1]}{pnum}"
        return nextname


class VideoSeries(VimeoRecord):
    videos = mdb.ListField(mdb.ReferenceField(Video, mdb.PULL))

    @classmethod
    def create_or_update(cls, ainfo):
        alb = cls.objects(uri=ainfo['uri']).first()
        if alb:
            alb = alb.synchronized()
        else:
            alb = VideoSeries(uri=ainfo['uri'], 
                              name=ainfo['name'],
                              html=ainfo['embed']['html'],
                              create_date=ainfo['created_time'],)
            alb._sync_vids()
            alb.save()
        return alb


    @classmethod
    def named(cls, aname):
        return cls.objects(name=aname).first()

    @classmethod
    def add_new(cls, aname, adescription):
        if VideoSeries.objects(name=aname).count() > 0:
            raise Exception(f"VideoSeries {aname} already exists.")
        resp = vcpost('/me/albums', name=aname, description=adescription).json()
        alb = VideoSeries(uri=resp['uri'], 
                          name=resp['name'],
                          html=resp['embed']['html'],
                          create_date=resp['created_time'],)
        alb.save()
        return alb

    def up_form_gen(self, vid_name, vid_desc, redir="/"):
        vp = vcpost("/me/videos", 
                    **dict(name=vid_name,
                           description=vid_desc,
                           upload=dict(approach="post", redirect_url=redir)))
        vp = vp.json()
        return vp['upload']['form']

    def add_video(self, viduri):
        vcput(f"{self.id}{viduri}")
        vid = Video.objects(uri=viduri).first()
        return vid

    def get_video_named(self, vname):
        return { x.name:x for x in self.videos }[vname]

    def remove(self):
        vimeourl = self.uri
        self.delete()
        vcdel(vimeourl) 

    @classmethod
    def sync_all(cls):
        global status
        if status == 'ready':
            lainfo = vcget('/me/albums', 
                           fields="uri,name,embed,created_time",
                           sort="date",
                           direction="desc").json()
            while('data' in lainfo):
                for ainfo in lainfo['data']: 
                    try:
                        status = VideoSeries.create_or_update(ainfo).name
                    except mdb.ValidationError as mve:
                       print(f"Skipping import of {ainfo['name']} due to {mve}")
                nextpage = lainfo.get('paging', {}).get('next', False)
                if nextpage:
                    lainfo = vcget(nextpage).json()
                else:
                    lainfo = {}
            status = 'ready'

    def synchronized(self):
        ainfo = vcget(self.uri,
                      fields="uri,name,embed,created_time",
                      sort="date",
                      direction="desc").json()
        self.name=ainfo['name']
        self.html=ainfo['embed']['html']
        self._sync_vids()
        self.save()
        return self

    def _sync_vids(self):
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
                except mdb.ValidationError as mve:
                   print(f"Skipping import of {vinfo['name']} due to {mve}")
            nextpage = vlinfo.get('paging', {}).get('next', False)
            if nextpage:
                vlinfo = vcget(nextpage).json()
            else:
                vlinfo = {}

def _drop_all():
    VideoSeries.drop_collection()
    Video.drop_collection()
    VimeoRecord.drop_collection()

