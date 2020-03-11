import os, flask_mongoengine, vimeo
from datetime import datetime

status = "N/A"
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
    if resp.status_code > 399:
        raise Exception(f"Vimeo Response: {resp.json()}")
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


class VideoRecord(VimeoRecord):
    albums = mdb.ListField(mdb.ReferenceField('AlbumRecord'))
    duration = mdb.IntField(required=True)
   
    def update(self, name, albums):
        if name != self.name:
            self.name = name

        vainfo = vcget(f"{self.uri}/albums/").json()
        while('data' in vainfo):
            for ainfo in vainfo['data']: 
                alb = AlbumRecord.objects(uri=ainfo['uri']).first()
                if not alb:
                    alb = AlbumRecord(uri=ainfo['uri'], 
                                      name=ainfo['name'],
                                      html=ainfo['embed']['html'],
                                      create_date=ainfo['created_time'],)
                    alb.save()
                if alb not in self.albums: 
                    self.albums.append(alb)
                    updated=True
            updated=True
        return updated
        
    @classmethod 
    def matching_id(cls, vimid):
        return cls.objects(uri=f"/videos/{vimid}").first()

    @property
    def album(self):
        return self.albums[0]

    def delete(self):
        super().delete()

    @property
    def next_name(self):
        nextname = f"{self.name} #2"
        npart = self.name.partition("#")
        if npart[2]:
            pnum = int(npart[2])+1
            nextname = f"{npart[0]}{npart[1]}{pnum}"
        return nextname


class AlbumRecord(VimeoRecord):
    videos = mdb.ListField(mdb.ReferenceField(VideoRecord))

    @classmethod
    def named(cls, aname):
        return cls.objects(name=aname).first()

    @classmethod
    def addAlbum(cls, aname, adescription):
        if AlbumRecord.objects(name=aname).count() > 0:
            raise Exception(f"Series {aname} already exists.")
        resp = vcpost('/me/albums', 
                      name=aname, 
                      description=adescription).json()
        alb = AlbumRecord(uri=resp['uri'], 
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

    def addVideo(self, viduri):
        vcput(f"{self.id}{viduri}")
        self.synchronize()

    def delete(self):
        super().delete()
        vcdel(self.uri) 

    def videoNamed(self, vname):
        return { x.name:x for x in self.videos }[vname]

    def synchronize(self):
        avinfo = vcget(f"{self.uri}/videos",
                       fields="uri,name,embed,created_time,duration,"
                             +"metadata.connections.albums",
                       sort="date",
                       direction="asc").json()
        if 'data' in avinfo: 
            self.videos.clear()
        while ('data' in avinfo):
            for vinfo in avinfo['data']:
                try:
                    vid = VideoRecord.objects(uri=vinfo['uri']).first()
                    if not vid: 
                        vid = VideoRecord(uri=vinfo['uri'], 
                                          name=vinfo['name'],
                                          html=vinfo['embed']['html'],
                                          create_date=vinfo['created_time'],
                                          duration=vinfo['duration'])
                        print(f"Created vid {vid.name} "
                            + f"for album {self.name}")
                    else:
                        #Update existing vid with any potential changes...
                        vid.name = vinfo['name']
                    self.videos.append(vid)
                    if self not in vid.albums: vid.albums.append(self)
                    vid.save()
                except mdb.ValidationError as mve:
                   print(f"Skipping import of {vinfo['name']} due to {mve}")
            nextpage = avinfo.get('paging', {}).get('next', False)
            if nextpage:
                avinfo = vcget(nextpage).json()
            else:
                avinfo = {}
        self.save()
        return len(self.videos)


def reset_and_resync_all():
    AlbumRecord.drop_collection()
    VideoRecord.drop_collection()
    VimeoRecord.drop_collection()
    sync_mongo_and_vimeo()

def sync_mongo_and_vimeo():
    lainfo = vcget('/me/albums', 
                   fields="uri,name,embed,created_time",
                   sort="date",
                   direction="desc").json()
    if 'data' not in lainfo: 
        raise RuntimeError("No data response from vimeo.")
    while('data' in lainfo):
        for ainfo in lainfo['data']: 
            try:
                alb = AlbumRecord.objects(uri=ainfo['uri']).first()
                if not alb:
                    alb = AlbumRecord(uri=ainfo['uri'], 
                                      name=ainfo['name'],
                                      html=ainfo['embed']['html'],
                                      create_date=ainfo['created_time'],)
                    alb.save()
                alb.synchronize()
                print(f"Processed {alb.name}")
                status=alb.name
            except mdb.ValidationError as mve:
               print(f"Skipping import of {ainfo['name']} due to {mve}")
        nextpage = lainfo.get('paging', {}).get('next', False)
        if nextpage:
            lainfo = vcget(nextpage).json()
        else:
            lainfo = {}
