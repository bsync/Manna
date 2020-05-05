import vidstore as vs
import datetime as dt
from flask_mongoengine import MongoEngine

db = MongoEngine()

def init_flask(app):
    db.init_app(app)

def init_db():
    ShowCase.drop_collection()
    VideoSeries.drop_collection()
    Video.drop_collection()
    VimeoRecord.drop_collection()

class VimeoRecord(db.Document):
    meta = {'allow_inheritance': True}
    uri = db.StringField(required=True, primary_key=True)
    name = db.StringField(required=True)
    description = db.StringField()
    create_date = db.DateField(required=True, default=dt.datetime.utcnow)
    fields="uri,name,created_time"

    @classmethod
    def named(cls, aname):
        match = cls.objects(name=aname).first()
        if not match:
            for x in cls.sync_gen():
                if x.name == aname: break
            match = cls.objects(name=aname).first()
        return match

    @classmethod
    def sync_gen(cls, vsuri=None, sfields=None, rcnt=None):
        if vsuri is None: vsuri = cls.VSURI
        if sfields is None: sfields = cls.fields
        yield "Syncronizing ..."
        sinfo = vs.get(vsuri, fields=sfields, sort="date", direction="desc")
        while('data' in sinfo):
            for vsinfo in sinfo['data']: 
                try:
                   obj = cls.objects(uri=vsinfo['uri']).first()
                   if obj:
                       obj.update(vsinfo)
                   else:
                       obj = cls.from_info(vsinfo)
                   yield "Synchronized ..." + obj.name 
                except db.ValidationError as mve:
                   print(f"{mve}: Skipping import of {vsinfo['name']}")
                if rcnt == 0: break
                elif rcnt is not None and rcnt > 0: rcnt -= 1
            if rcnt == 0: break
            nextpage = sinfo.get('paging', {}).get('next', False)
            if nextpage:
                sinfo = vs.get(nextpage)
            else:
                sinfo = {}
        yield "done!"


class Video(VimeoRecord):
    VSURI="/me/videos"
    fields="uri,name,embed,files,download," \
          +"created_time,duration," \
          +"pictures.sizes.link," \
          +"metadata.connections.albums"
    series = db.ReferenceField('VideoSeries')
    duration = db.IntField(required=True)
    html = db.StringField()
    vlink = db.StringField(required=True)
    dlink = db.StringField(required=True)
    plink = db.StringField(required=True)

    @classmethod
    def latest(cls, cnt):
        list(VideoSeries.sync_gen(rcnt=1))
        return cls.objects.order_by('-create_date')[:cnt]

    @classmethod
    def from_info(cls, vinfo):
        vid = Video(uri=vinfo['uri'], 
                    name=vinfo['name'],
                    html=vinfo['embed']['html'],
                    vlink=vinfo['files'][0]['link'],
                    dlink=vinfo['download'][0]['link'],
                    plink=vinfo['pictures']['sizes'][0]['link'],
                    create_date=vinfo['created_time'],
                    duration=vinfo['duration'])
        print(f"Created new Video from vimeo source {vid.name}")
        vid.save()
        return vid

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

    def update(self, vinfo):
        self.name = vinfo['name']
        self.html = vinfo['embed']['html']
        self.vlink = vinfo['files'][0]['link']
        self.dlink = vinfo['download'][0]['link']
        self.plink = vinfo['pictures']['sizes'][0]['link']
        self.save()

class VideoSeries(VimeoRecord):
    VSURI="/me/projects"
    videos = db.ListField(db.ReferenceField(Video, db.PULL))

    @classmethod
    def sync_new(cls, aname, adescription):
        if cls.objects(name=aname).count() > 0: 
            raise Exception(f"VideoSeries {aname} already exists.")
        resp = vs.post(cls.VSURI, name=aname, description=adescription)
        alb = cls(resp)
        return alb

    @classmethod
    def from_info(cls, vsinfo):
        series = VideoSeries(uri=vsinfo['uri'], 
                             name=vsinfo['name'],
                             create_date=vsinfo['created_time'],)
        series.sync_vids()
        series.save()
        return series

    def update(self, vsinfo=None):
        if vsinfo is None:
            vsinfo = vs.get(f"{self.uri}",
                            fields=self.fields,
                            sort="date",
                            direction="asc")
        self.name = vsinfo['name']
        self.sync_vids()

    def start_upload(self, vid_name, vid_desc, redir="/"):
        yield "Waiting for upload to begin..."
        vp = vs.post("/me/videos", 
                    **dict(name=vid_name,
                           description=vid_desc,
                           upload=dict(approach="post", redirect_url=redir)))
        return vp['upload']['upload_link']

    def finish_upload(self, viduri):
        yield "Upload complete waiting for vid to become avaialble..."
        resp = vs.put(f"{self.id}{viduri}")
        if resp.ok:
            resp = vs.get(viduri)
            secs = 0
            while  resp['status'] != 'available':
                time.sleep(5)
                secs += 5
                resp = vs.get(viduri)
                yield f"Status after {secs} seconds: {resp['status']}"
        self.sync_vids()
        yield "done!"

    def video_named(self, vname):
        return { x.name:x for x in self.videos }[vname]

    def remove(self):
        vimeourl = self.uri
        self.delete()
        vs.delete(vimeourl) 

    def sync_vids(self):
        vlinfo = vs.get(f"{self.uri}/videos",
                        fields=Video.fields,
                        sort="date",
                        sizes="1280x720,1920x1080",
                        direction="asc")
        if 'data' in vlinfo: 
            self.videos.clear()
        while ('data' in vlinfo):
            for vinfo in vlinfo['data']:
                try:
                    vid = Video.objects(uri=vinfo['uri']).first()
                    if vid:
                        vid.update(vinfo)
                    else:
                        vid = Video.from_info(vinfo)
                    self.videos.append(vid)
                    vid.series = self
                    vid.save()
                except db.ValidationError as mve:
                   print(f"Skipping import of {vinfo['name']} due to {mve}")
            nextpage = vlinfo.get('paging', {}).get('next', False)
            if nextpage:
                vlinfo = vs.get(nextpage)
            else:
                vlinfo = {}
        self.save()

    def replace_videos(self, vids):
        vuri_list = ",".join([ v.uri for v in vids ])
        resp = vs.put(f'{self.uri}/videos', videos=vuri_list)
        for vid in self.videos:
            vs.put(f"{self.uri}{vid.uri}")
            print(f"Added lesson {vid.name} to roku showcase")
        #self.sync_vids()

class ShowCase(VideoSeries):
    VSURI="/me/albums"

    @classmethod
    def from_info(cls, vsinfo):
        case = ShowCase(uri=vsinfo['uri'], 
                         name=vsinfo['name'],
                         create_date=vsinfo['created_time'],)
        case.sync_vids()
        case.save()
        return case
