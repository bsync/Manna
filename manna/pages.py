import os, flask, traceback, json
from flask.globals import _app_ctx_stack, _request_ctx_stack
from werkzeug.urls import url_parse
from flask import url_for
from collections import namedtuple
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap
from . import forms

class Mannager:
    def __init__(self, app):
        Bootstrap(app)
        CSRFProtect(app)

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
                self.video = mstore.video_by_id(int(kwargs['video_id']))
            elif 'audio_id' in kwargs:
                self.audio = mstore.audio_by_id(int(kwargs['audio_id']))
            elif 'dt_json' in kwargs:
                self.json = self._dt_json(**kwargs)

        @property
        def is_playable(self):
            return self.has_video or self.has_audio

        @property
        def has_video(self):
            return hasattr(self, 'video')

        @property
        def has_audio(self):
            return hasattr(self, 'audio')

        @property
        def has_json(self):
            return hasattr(self, 'json')

        @property
        def needs_vimeo(self):
            return 'vimeo' in str(type(self.mstore))

        @property
        def template_name(self):
            return f"{self.__class__.__name__}.html"

        @property
        def response(self):
            if self.has_json: 
                return self.json
            elif self.has_audio:
                return flask.Response(self.audio, mimetype="audio/mpeg")
            else:
                return flask.render_template(self.template_name, page=self)


    class VideoPlayer(MannaStorePage):
        pass

    class CatalogStorePage(MannaStorePage):

        @property
        def catalog(self):
            return self.mstore.catalog()


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
        def __init__(self, mstore):
            super().__init__(mstore)
            asform = self.add(forms.AddSeriesToCatalogForm())
            if asform.was_submitted:
                mstore.add_new_series(asform.series_name.data)
            

    class SeriesPage(MannaStorePage):
        def __init__(self, mstore, series, **kwargs):
            self.series = mstore.series_by_name(series)
            super().__init__(mstore, **kwargs)

        def _dt_json(self, **kwargs):
            sort=kwargs.get(f"columns[{kwargs.get('order[0][column]', 0)}][data]", False)
            if sort == 'name':
                kwargs[f"columns[{kwargs.get('order[0][column]', 0)}][data]"] = 'alphabetical'
            svids = self.series.videos(**kwargs) 
            qdicts = [ dict(id=id(x),
                       date=x.date.strftime("%Y-%m-%d"), 
                       name=x.described, 
                       duration=str(x.duration)) for x in svids ]
            return json.dumps(dict(
                data=qdicts,
                draw=int(kwargs['draw']), 
                recordsTotal=svids.available, 
                recordsFiltered=svids.available))


    class SeriesEditPage(SeriesPage):
        def __init__(self, mstore, series, **kwargs):
            super().__init__(mstore, series, **kwargs)
            self.token = mstore.token
            if 'dt_json' not in kwargs:
                self.add_videos_form = self.add(forms.AddVideoSet(self.series))
                self.purge_video_form = self.add(forms.PurgeVideo(self.series))
                self.redate_series_form = self.add(forms.RedateSeries(self.series))
                self.normalize_series_form = self.add(forms.NormalizeTitles(self.series))
                #self.sync_series_form = self.add(forms.SyncSeries(self.series))


    class LoginPage(MannaPage):
        def __init__(self, access_manager):
            super().__init__("Login")
            self.login_form = self.add(forms.LoginUserForm(access_manager))
            self.glogin_form = self.add(forms.GoogleLoginForm())
            self.request_form = self.add(forms.RequestAccessForm())
            self.invite_form = self.add(forms.InviteUserForm())

        @property
        def login_form_was_submitted(self):
            return self.login_form.was_submitted

        @property
        def request_form_was_submitted(self):
            return self.request_form.was_submitted

        @property
        def invite_access_form_was_submitted(self):
            return self.invite_form.was_submitted

        @property
        def google_login_form_was_submitted(self):
            return self.glogin_form.was_submitted

        @property
        def email(self):
            if self.login_form_was_submitted:
                return self.login_form.email.data
            elif self.request_form_was_submitted:
                return self.request_form.email.data
            else:
                return None

        @property
        def password(self):
            if self.login_form_was_submitted:
                return self.login_form.password.data
            else:
                return None

        @property
        def comments(self):
            if self.request_form_was_submitted:
                return self.request_form.comments.data
            else:
                return None
        

    class RegistrationPage(MannaPage):
        def __init__(self, access_manager):
            super().__init__("Login")
            self.users = access_manager.datastore.find_users()
            self.register_form = self.add(forms.RegisterUserForm())

        @property
        def register_user_form_was_submitted(self):
            return self.register_form.was_submitted

        @property
        def selected_user(self):
            sid = self.register_form.user_selection
            return self.datastore.find_user(email=sid) if sid else None

        @property
        def operation(self):
            for op in "register unregister promote demote delete".split():
                if op in flask.request.form:
                    return flask.request.form[op]
            return None

        def roles_for_user(self, user):
            return [ r.name for r in user.roles ]


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


