import os, flask, traceback
import forms
from flask.globals import _app_ctx_stack, _request_ctx_stack
from werkzeug.urls import url_parse
from tables import VideoTable, CatalogTable
from players import VideoPlayer
from datetime import datetime, timezone
from dominate.util import raw
from pathlib import Path
from flask import url_for

class MannaPage(list):
    css = ["Page.css"]
    scripts = []
    style = ""
    def __init__(self, title='Manna'):
        self.title = title if title else self.__class__.__name__
        if flask.current_app.env == "development":
            self.title = self.title + " (dev) "
        if self.title.startswith('/'):
            _, _, title = self.title.rpartition('/')
            self.title = f'<a href="{self.title}" onclick="shift_edit(event, this)">{title}</a>'
        self.scriptage = ""
        self.template_vars = dict(page=self)
        self.css = self.css.copy()
        self.scripts = self.scripts.copy()
        
    @property
    def site_name(self):
        return flask.current_app.config.get('TITLE', 'Manna')

    @property
    def breadcrumbs(self):
        return BreadCrumbs(flask.request)

    @property
    def response(self):
        if hasattr(self, '_json'):
            return self._json
        rendered = []
        for component in self:
            if isinstance(component, forms.MannaForm):
                if component.was_submitted:
                    try:
                        component.on_validated()
                    except Exception as e:
                        emsg = str(e) + traceback.format_exc()
                        flask.flash(f"Operation failed for {self}: {emsg}")
            if hasattr(component, 'redirection'):
                return component.redirection
            if hasattr(component, 'template'):
                rstr = flask.render_template(component.template, **component.template_vars)
                name = getattr(component, 'name', component.__class__.__name__)
                rendered.append((name, rstr))
        for idx,css in enumerate(self.css):
            if not css.startswith("http"):
                self.css[idx] = url_for('static', filename=css)
        for idx,script in enumerate(self.scripts):
            if not script.startswith("http"):
                self.scripts[idx] = url_for('static', filename=script)
        return flask.render_template("page.html", 
                                     prerendered=rendered, 
                                     **self.template_vars)

    def add(self, component):
        if hasattr(component, 'css'):
            for css in component.css:
                if css not in self.css:
                    self.css.append(css)
        if hasattr(component, 'style'):
            self.style += component.style
        if hasattr(component, 'scripts'):
            for script in component.scripts:
                if script not in self.scripts:
                    self.scripts.append(script)
        if hasattr(component, 'scriptage'):
            self.scriptage = f"{self.scriptage}\n{component.scriptage}\n"
        self.append(component)
        return component

    def show_errors(self, *errs):
        for msg in errs:
            flask.flash(msg)

    def roku(self, vids):
        tstamp = datetime.now(tz=timezone.utc)
        tstamp = tstamp.isoformat(timespec="seconds")
        rfeed = dict(
            providerName="Pleroma Videos",
            lastUpdated=tstamp,
            language='en',
            movies=[dict(id=x.uri.split('/')[2],
                        title=f"{x.parent_name}-{x.name}",
                        genres=["faith"],
                        tags=["faith"],
                        thumbnail=x.plink,
                        content=dict(
                             dateAdded=x.date.strftime("%Y-%m-%d"),
                             duration=x.duration,
                             videos=[
                                dict(url=x.vlink, 
                                     quality="HD", 
                                     videoType="MP4"), ],
                             ),
                       releaseDate=tstamp,
                       shortDescription=x.parent_name,)
                    for i,x in enumerate(vids) ],)
        return flask.jsonify(rfeed)

    def play_series(self, series):
        with self.content:
            tags.div(raw(series.html), id="player")
        return self.response


class VideoListPage(MannaPage):
    def __init__(self, title, vids):
        super().__init__(title)
        self.add(VideoTable(vids=vids))

class VideoPage(MannaPage):
    def __init__(self, title, vid):
        super().__init__(title)
        self.add(VideoPlayer(vid))


class CatalogPage(MannaPage):
    def __init__(self, mstore, ajax=None, **kwargs):
        super().__init__("Catalog")
        if ajax: #This is a full page request 
            self.add(
                CatalogTable(ajax=f"'{ajax}'", 
                             serverSide="true", 
                             **kwargs))
        else:#This is a request for json only
            cdir = kwargs['direction'] = kwargs['order[0][dir]'] #table's sort direction
            ocidx = int(kwargs['order[0][column]']) #table's current column sort idx
            if 'search[value]' in  kwargs:
                kwargs['query'] = kwargs.pop('search[value]') 
            if ocidx < 2:
                kwargs['sort'] = ['modified_time', 'name'][ocidx]
                pcat = pcatpage = mstore.catalog(**kwargs)
            else:
                pcat = mstore.catalog() #Must get entire catalog to order by video_count
                pcat.sort(key=lambda x: x.video_count, reverse=(cdir == 'asc'))
                pcat_start = int(kwargs['start'])
                pcatpage = pcat[pcat_start:pcat_start+int(kwargs['length'])]
            self._json = flask.jsonify(
                dict(data=[[ser.date.strftime("%Y-%m-%d"), 
                            f"<a href={url_for('.show_series_page', series=ser.name)}>{ser.name}</a>", 
                            ser.video_count ] for ser in pcatpage],
                    draw=int(kwargs['draw']), 
                    recordsTotal=pcat.available, 
                    recordsFiltered=pcat.available))


class CatalogEditPage(CatalogPage):
    def __init__(self, cat, **kwargs):
        super().__init__("Edit Catalog")
        self.add(forms.AddSeriesToCatalogForm("Add Series"))
        self.add(forms.SyncWithCatalogForm("Sync Catalog"))
        self.add(CatalogTable(cat, **kwargs))

class SeriesPage(MannaPage):
    def __init__(self, series, ajax=None, **kwargs):
        super().__init__(f"Series {series.name}")
        if ajax:
            self.add(VideoTable(ajax=f"'{ajax}'", serverSide="true"))
        else:
            ocolidx = int(kwargs['order[0][column]']) #table's current column sort idx
            kwargs['sort'] = ['date', 'alphabetical', 'alphabetical', 'duration'][ocolidx]
            kwargs['direction'] = kwargs['order[0][dir]']
            vids = series.videos(**kwargs)
            self._json = flask.jsonify(
                dict(data=[[vid.date.strftime("%Y-%m-%d"), 
                            vid.parent_name, 
                            f"<a href={url_for('.play_restricted', series=series.name, video=vid.name)}>{vid.name}</a>", 
                            vid.duration ] for vid in vids],
                    draw=int(kwargs['draw']), 
                    recordsTotal=series.video_count, 
                    recordsFiltered=series.video_count))

class SeriesEditPage(SeriesPage):
    def __init__(self, series, **kwargs):
        super().__init__(series, **kwargs)
        self.add(forms.AddVideoSetForm(series))
        self.add(forms.PurgeVideoFromSeries(series))
        self.add(forms.RedateSeriesForm(series))
        self.add(forms.NormalizeSeries(series))
        self.add(forms.SyncWithSeriesForm(series))


class LoginPage(MannaPage):
    def __init__(self, login_manager):
        super().__init__("Login")
        self.add(forms.LoginUserForm(login_manager))
        self.add(forms.GoogleLoginForm(login_manager))
        self.add(forms.RequestAccessForm(login_manager))


class RegistrationPage(MannaPage):
    def __init__(self, login_manager):
        super().__init__("Registration")
        self.add(forms.RegistrationForm(login_manager))
        self.add(forms.InviteUserForm(login_manager))


class AudioPage(MannaPage):
    def __init__(self, video):
        super().__init__(f"Play or Download Audio")
        self.video = video

    @property
    def response(self):
        def generate_mp3():
            import subprocess as sp
            ffin = f' -i "{self.video.vlink}" '
            ffopts = " -af silenceremove=1:1:.01 "
            ffopts += "-ac 1 -ab 64k -ar 44100 -f mp3 "
            ffout = ' - '
            ffmpeg = 'ffmpeg' + ffin + ffopts + ffout
            tffmpeg = "timeout -s SIGKILL 300 " + ffmpeg 
            with sp.Popen(tffmpeg, shell=True,
                          stdout = sp.PIPE, stderr=sp.PIPE,
                          close_fds = True, preexec_fn=os.setsid) as process:
                while process.poll() is None:
                    yield process.stdout.read(1000)
        return flask.Response(generate_mp3(), mimetype="audio/mpeg")


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
        elif self._part == self.req.script_root:
            self.name = self._part[1:]
            self._part = self.req.path[1:]
            self.url = self.req.root_url[:-1]
        elif self.req.path.endswith(self._part):
            self.name, _, self._part = self._part.partition('/')
            if self.name:
                self.url = f"{self.url}/{self.name}"
            while not self.is_valid_url(self.url): #Skip intermediate urls if they are invalid
                self.name, _, self._part = self._part.partition('/')
                self.url = f"{self.url}/{self.name}"
        if not self.name:
            raise StopIteration
        return self

class ErrorPage(MannaPage):
    def __init__(self, err):
        super().__init__("Trouble in Paradise...")
        flask.flash(err)

