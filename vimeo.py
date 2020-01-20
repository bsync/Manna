import os, sys, subprocess, requests, urllib, pathlib
import flask_mongoengine 
from ffmpy import FFmpeg
from concurrent.futures import ThreadPoolExecutor
from dateutil.parser import parse as dparse
from datetime import datetime

mdb = flask_mongoengine.MongoEngine()

def vimeo_fetch(aurl, fparams=None, ah={}):
    ah.update(Host='api.vimeo.com')
    ah.update(Authorization='bearer {}'.format(os.getenv("VIMEO_TOKEN")))
    return requests.get('https://api.vimeo.com' 
                        + aurl, params=fparams, 
                        headers=ah).json()

class VimeoRecord(mdb.Document):
    meta = {'allow_inheritance': True}
    uri = mdb.StringField(required=True, primary_key=True)
    name = mdb.StringField(required=True)
    html = mdb.StringField(required=True)
    create_date = mdb.DateField(required=True, default=datetime.utcnow)

    @property
    def vimid(self):
        return int(self.uri.rpartition('/')[2])

    @classmethod
    def latest(cls, cnt):
        sync_latest()
        return cls.objects().order_by('-create_date')[:cnt]


class VideoRecord(VimeoRecord):
    albums = mdb.ListField(mdb.ReferenceField('AlbumRecord'))
    duration = mdb.IntField(required=True)
   
    @classmethod 
    def matching_id(cls, vimid):
        return cls.objects(uri=f"/videos/{vimid}").first()

    @property
    def album(self):
        return self.albums[0]

    def describe(self):
        return (f"VideoRecord of {self.name}" + 
                f" dated {self.create_date} from album {self.albums}")


class AlbumRecord(VimeoRecord):
    videos = mdb.ListField(mdb.ReferenceField(VideoRecord))

    @classmethod
    def named(cls, aname):
        return cls.objects(name=aname).first()

    def videoNamed(self, vname):
        return { x.name:x for x in self.videos }[vname]

    def synchronize(self):
        avinfo = vimeo_fetch(f"{self.uri}/videos",
                             fparams={'fields': "uri,name,embed,created_time,duration,"
                                              + "metadata.connections.albums",
                                       'sort': "date",
                                       'direction': "desc"})
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
                        print(f"Created video {vid.name} for album {self.name}")
                    if vid not in self.videos: self.videos.append(vid)
                    if self not in vid.albums: vid.albums.append(self)
                    vid.save()
                    self.save()
                except mdb.ValidationError as mve:
                   print(f"Skipping import of {vinfo['name']} due to {mve}")
            nextpage = avinfo.get('paging', {}).get('next', False)
            if nextpage:
                avinfo = vimeo_fetch(nextpage)
            else:
                avinfo = {}
    
        return len(self.videos)

    def describe(self):
        return (f"AlbumRecord of {self.name} dated {self.create_date}" +
                f"containing videos {self.vidoes}")

def reset_and_resync_all():
    AlbumRecord.drop_collection()
    VideoRecord.drop_collection()
    VimeoRecord.drop_collection()
    sync_latest()

def sync_latest():
    lainfo = vimeo_fetch('/me/albums', 
                         fparams={'fields': "uri,name,embed,created_time",
                                  'sort': "date",
                                  'direction': "desc"})
    if 'data' not in lainfo: raise RuntimeError("No data response from vimeo.")
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
                # If the synchronize effort adds no new videos to the latest
                # modified album then we must be done
                if len(alb.videos) == alb.synchronize(): break 
            except mdb.ValidationError as mve:
               print(f"Skipping import of {ainfo['name']} due to {mve}")
        nextpage = lainfo.get('paging', {}).get('next', False)
        if nextpage:
            lainfo = vimeo_fetch(nextpage)
        else:
            lainfo = {}

