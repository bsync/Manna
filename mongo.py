import re, time
import vidstore as vs
import datetime as dt
from flask_mongoengine import MongoEngine
from datetime import timedelta

db = MongoEngine()

def init_flask(app):
    db.init_app(app)

def init_db():
    ShowCase.drop_collection()
    VideoSeries.drop_collection()
    Video.drop_collection()
    VimeoRecord.drop_collection()

class User(db.Document):
    id_= db.StringField(primary_key=True)
    name = db.StringField(required=True)
    email = db.EmailField(required=True)
    profile_pic = db.StringField(required=True)
    is_active = db.BooleanField(default=False)
    is_anonymous = db.BooleanField(default=False)

    def get_id(self):
        return self.id_

    @property
    def is_authenticated(self):
        return self.is_active

def video_for(named_series, named_video):
    series = VideoSeries.named(named_series)
    return series.video_named(named_video)

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
            cls.sync_gen()
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
                       obj.sync_with_vimeo(vsinfo)
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
        yield "Finished"

    def remove(self):
        vimeourl = self.uri
        self.delete()


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
        """ Match one or more digits in the middle of the video's current name
            and replace it with value of the digits incremented by one
        """
        return re.sub(
                r"(.*\D+)(\d+)(.*)",  
                lambda x: x.group(1) + str(int(x.group(2)) + 1) + x.group(3),  
                self.name) 

    def sync_with_vimeo(self, vinfo):
        self.name = vinfo['name']
        self.html = vinfo['embed']['html']
        self.vlink = vinfo['files'][0]['link']
        self.dlink = vinfo['download'][0]['link']
        self.plink = vinfo['pictures']['sizes'][0]['link']
        self.save()

class VideoSeries(VimeoRecord):
    VSURI="/me/projects"
    videos=db.ListField(db.ReferenceField(Video, reverse_delete_rule=db.PULL))

    @classmethod
    def unlisted_series(cls):
        sinfo = vs.get(cls.VSURI, 
                       fields=cls.fields, 
                       sort="date", 
                       direction="desc")
        while('data' in sinfo):
            for vsinfo in sinfo['data']: 
                if not cls.objects(uri=vsinfo['uri']).first():
                    yield vsinfo
            nextpage = sinfo.get('paging', {}).get('next', False)
            if nextpage:
                sinfo = vs.get(nextpage)
            else:
                sinfo = {}

    @classmethod
    def import_series(cls, select, sdate):
        select['created_date'] = sdate.data.isoformat()
        series = cls.from_info(select)
        series.upDateVids(sdate.data)
        return series

    @classmethod
    def sync_new(cls, aname, adescription):
        if cls.objects(name=aname).count() > 0: 
            raise Exception(f"VideoSeries {aname} already exists.")
        resp = vs.post(cls.VSURI, name=aname, description=adescription)
        return cls.from_info(resp)

    @classmethod
    def from_info(cls, vsinfo):
        series = VideoSeries(uri=vsinfo['uri'], 
                             name=vsinfo['name'],
                             create_date=vsinfo['created_time'],)
        series.sync_vids()
        series.save()
        return series

    def sync_with_vimeo(self, vsinfo=None):
        if vsinfo is None:
            vsinfo = vs.get(f"{self.uri}",
                            fields=self.fields,
                            sort="date",
                            direction="asc")
        self.name = vsinfo['name']
        self.save()
        self.sync_vids()

    def uplink(self, vid_name, vid_desc, redir="/"):
        vp = vs.post("/me/videos", 
                     name=vid_name,
                     description=vid_desc,
                     upload=dict(approach="post", redirect_url=redir))
        return vp['upload']['upload_link']

    def process_upload(self, vidName, recDate, vidUri):
        yield f"Waiting for {vidName} to become available"
        resp = vs.put(f"{self.id}{vidUri}")
        if resp.ok:
            resp = vs.get(vidUri)
            secs = 0
            while  resp['status'] != 'available':
                time.sleep(5)
                secs += 5
                resp = vs.get(vidUri)
                status = resp['status']
                if secs%2:
                    yield f"Processing {vidName} upload to {self.name}"
                else:
                    yield f"{vidName} status after {secs/60:.2f} minutes: {status}"
            vid = Video.from_info(resp)
            vid.update(create_date=recDate, dlink=resp['download'][0]['link'])
            vid.series = self
            vid.save()
            self.videos.append(vid)
            self.save()
        yield f"Finished upload processing for {vidName} of {self.name}!"

    def video_named(self, vname):
        return { x.name:x for x in self.videos }[vname]

    def sync_vids(self):
        vlinfo = vs.get(f"{self.uri}/videos",
                        fields=Video.fields,
                        sort="date",
                        sizes="1280x720,1920x1080",
                        direction="asc")
        if len(self.videos):
            self.update(pull_all__videos=self.videos)
            self.reload()
        while ('data' in vlinfo):
            for vinfo in vlinfo['data']:
                try:
                    vid = Video.objects(uri=vinfo['uri']).first()
                    if vid:
                        vid.sync_with_vimeo(vinfo)
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

    def upDateVids(self, sdate, start_vid=None, stop_vid=None, inc=3):
        for vid in self.videos:
            if start_vid:
                if vid.name != start_vid:
                    continue
                else:
                    start_vid = None
            vid.create_date = sdate
            sdate += timedelta(days=inc)
            vid.save()
            if stop_vid:
                if vid.name == stop_vid:
                    break

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
