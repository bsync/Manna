import os, flask, traceback, forms
from flask.globals import _app_ctx_stack, _request_ctx_stack
from werkzeug.urls import url_parse
from flask import url_for
from collections import namedtuple
import json

class MannaPage(list):
    def __init__(self, title="Manna"):
        super().__init__()
        self.title = title

    @property
    def site_name(self):
        return flask.current_app.config.get('TITLE', 'Manna')

    @property
    def breadcrumbs(self):
        return BreadCrumbs(flask.request)

    @property
    def forms(self):
        return filter(lambda x : isinstance(x, forms.MannaForm), self)

    def add(self, component):
        self.append(component)
        return component

    def show_errors(self, *errs):
        for msg in errs:
            flask.flash(msg)


class MannaStorePage(MannaPage):

    def __init__(self, mstore, **kwargs):
        super().__init__()
        self.mstore = mstore
        if 'video_id' in kwargs:
            self.video = mstore.video_by_id(kwargs['video_id'])
        elif 'audio_id' in kwargs:
            self.audio = mstore.audio_by_id(kwargs['audio_id'])
        elif 'dt_json' in kwargs:
            self.json = self._dt_json(**kwargs)

    @property
    def is_playable(self):
        return hasattr(self, 'video') or hasattr(self, 'audio')

    @property
    def has_audio(self):
        return hasattr(self, 'audio')

    @property
    def has_json(self):
        return hasattr(self, 'json')

    def _dt_json(self, **kwargs):
        cseries = self.mstore.catalog(**kwargs)
        qdicts = [ dict(id=x.id,
                   date=x.date.strftime("%Y-%m-%d"), 
                   name=x.name, 
                   video_count=x.video_count) for x in cseries ]
        return json.dumps(dict(
            data=qdicts,
            draw=int(kwargs['draw']), 
            recordsTotal=cseries.available, 
            recordsFiltered=cseries.available))


class RecentVideosPage(MannaStorePage):

    def __init__(self, mstore, **kwargs):
        super().__init__(mstore, **kwargs)
        if hasattr(self, 'video') and self.video not in self.vids:
            raise Exception(f"{self.video.name} is not a recent video!")

    @property
    def vids(self):
        return self.mstore.recent_videos 


class EditRecentVideosPage(RecentVideosPage):

    def __init__(self, mstore, **kwargs):
        super().__init__(mstore, **kwargs)
        self.add(forms.AddToRecentVideosForm())

    @property
    def vids(self):
        return (self.mstore.latest_videos - self.mstore.recent_videos)[:5]

    def include_as_recent(self, video_id):
        video = self.mstore.video_by_id(video_id)
        if self.mstore.adjust_recents(video):
            return(f"Added {video.name} to recent videos: {video.date}")
        else:
            return(f"{video.name} of {video.date} is not recent enough!")


class CatalogEditPage(MannaStorePage):

    def __init__(self, mstore, title="Manna"):
        super().__init__(mstore, title)
        asform = self.add(forms.AddSeriesToCatalogForm())
        if asform.was_submitted:
            mstore.add_new_series(asform.series_name.data)
        

class SeriesPage(MannaStorePage):

    def __init__(self, mstore, series, **kwargs):
        self.series = mstore.series_by_name(series)
        super().__init__(mstore, **kwargs)

    def _dt_json(self, **kwargs):
        svids = self.series.videos(**kwargs) 
        qdicts = [ dict(id=x.id,
                   date=x.date.strftime("%Y-%m-%d"), 
                   name=x.name, 
                   duration=str(x.duration)) for x in svids ]
        return json.dumps(dict(
            data=qdicts,
            draw=int(kwargs['draw']), 
            recordsTotal=svids.available, 
            recordsFiltered=svids.available))


class SeriesEditPage(SeriesPage):

    def __init__(self, mstore, series, **kwargs):
        super().__init__(mstore, series, **kwargs)
        if 'dt_json' not in kwargs:
            self.add_videos_form = self.add(forms.AddVideoSet(self.series))
            self.purge_video_form = self.add(forms.PurgeVideo(self.series))
            self.redate_series_form = self.add(forms.RedateSeries(self.series))
            self.normalize_series_form = self.add(forms.NormalizeTitles(self.series))
            #self.sync_series_form = self.add(forms.SyncSeries(self.series))


class LoginPage(MannaPage):

    def __init__(self, login_manager):
        super().__init__("Login")
        self.login_form = self.add(forms.LoginUserForm(login_manager))
        self.glogin_form = self.add(forms.GoogleLoginForm())
        self.request_form = self.add(forms.RequestAccessForm())
        self.redirection = False
        if self.login_form.was_submitted:
            self.redirection = login_manager.login_via_email(
                self.login_form.email.data, 
                self.login_form.password.data)
        elif self.glogin_form.was_submitted:
            self.redirection = login_manager.login_via_google()
        elif self.request_form.was_submitted:
            self.redirection = login_manager.request_access()


class RegistrationPage(MannaPage):

    def __init__(self, login_manager):
        super().__init__("Registration")
        self.add(forms.RegistrationForm(login_manager))
        self.add(forms.InviteUserForm(login_manager))



class BreadCrumbs(object):
    def __init__(self, req):
        self.req = req

    def is_valid_url(self, url, method = None):
        appctx = _app_ctx_stack.top
        reqctx = _request_ctx_stack.top
        if appctx is None:
            raise RuntimeError('Attempted to match a URL without the '
                               'application context being pushed. This has to be '
                               'executed when application context is available.')

        if reqctx is not None:
            url_adapter = reqctx.url_adapter
        else:
            url_adapter = appctx.url_adapter
            if url_adapter is None:
                raise RuntimeError('Application was not able to create a URL '
                                   'adapter for request independent URL matching. '
                                   'You might be able to fix this by setting '
                                   'the SERVER_NAME config variable.')
        if flask.request.url_root.startswith(url):
            return False
        parsed_url = url_parse(url)
        if parsed_url.netloc != "" and parsed_url.netloc != url_adapter.server_name:
            return False
        try:
            return url_adapter.match(parsed_url.path[len(flask.request.script_root):], method)
        except Exception:
            return False

    def __iter__(self):
        self._part = self.req.host
        return self

    def __next__(self):
        self.name = None
        if self._part == self.req.host:
            self.name = self._part.partition('.')[0].upper()
            self._part = self.req.script_root
            self.url = f"https://{self.req.host}"
        if self._part == self.req.script_root:
            self.name = self._part[1:]
            self._part = self.req.path[1:]
            self.url = self.req.root_url[:-1]
        elif self.req.path.endswith(self._part):
            self.name, _, self._part = self._part.partition('/')
            if self.name:
                self.url = f"{self.url}/{self.name}"
            while self.name and (self.name == 'recent' or not self.is_valid_url(self.url)): #Skip intermediate urls if they are invalid
                self.name, _, self._part = self._part.partition('/')
                self.url = f"{self.url}/{self.name}"
        if not self.name:
            raise StopIteration
        return self


