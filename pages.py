import os
import flask
import dominate, dominate.tags as tags
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
    def response(self):
        rendered = []
        for component in self:
            if hasattr(component, 'redirect'):
                return component.redirect
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
        return self

    def show_errors(self, *errs):
        for msg in errs:
            flask.flash(msg)

    def redirect(self, url, to_form=None, with_msg=False, refresh=False, **kwargs): 
        if to_form is not None:
            to_form = to_form.id 
            url = f"{url}#{to_form}"
        if with_msg:
            if not isinstance(with_msg, str):
                with_msg = " ".join(with_msg)
            flask.flash(with_msg, to_form)
            self.on_ready.append(f'window.location.hash = "{to_form}"; ')
        if refresh:
            with self.doc.head:
                tags.meta(http_equiv="refresh", content=f"3;{flask.request.url}")
        url += "&".join([f"?{k}={v}" for k,v in kwargs.items()])
        self.redirection = flask.redirect(url)

    def roku(self, vids):
        tstamp = datetime.now(tz=timezone.utc)
        tstamp = tstamp.isoformat(timespec="seconds")
        rfeed = dict(
            providerName="Pleroma Videos",
            lastUpdated=tstamp,
            language='en',
            movies=[dict(id=x.uri.split('/')[2],
                        title=f"{x.parent_series_name}-{x.name}",
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
                       shortDescription=x.parent_series_name,)
                    for i,x in enumerate(vids) ],)
        return flask.jsonify(rfeed)

    def play_series(self, series):
        with self.content:
            tags.div(raw(series.html), id="player")
        return self.response


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


class ErrorPage(MannaPage):
    def __init__(self, err):
        super().__init__("Trouble in Paradise...")
        with self.content:
            tags.h2(err)
