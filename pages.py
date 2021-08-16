import sys, traceback, os, re
import flask, flask_login
import dominate, dominate.tags as tags
import executor, mannatags
from datetime import datetime, timezone
from dominate.util import raw
from pathlib import Path
from requests.models import PreparedRequest
from flask import url_for
from flask_wtf.csrf import CSRFProtect
from forms import Forms
from tables import VideoTable

class Pages(object):
    def __new__(cls, app, mstore):
        MannaPage.site_name = app.config.get("TITLE", "Manna")
        if app.env == "development":
            MannaPage.site_name = MannaPage.site_name + " (dev) "
        global forms, login
        csrf = CSRFProtect(app)
        forms = Forms(app, mstore)
        return sys.modules[__name__] #just use this module as the page manager


class MannaPage(list):
    css = ["Page.css"]
    scripts = []
    style = ""
    def __init__(self, title=''):
        self.title = title if title else self.__class__.__name__
        self.scriptage = ""
        self.template_vars = dict(page=self)
        self.css = self.css.copy()
        self.scripts = self.scripts.copy()

    def add(self, component):
        if hasattr(component, 'css'):
            self.css.extend([ c for c in component.css if c not in self.css ])
        if hasattr(component, 'style'):
            self.style += component.style
        if hasattr(component, 'scripts'):
            self.scripts.extend([ s for s in component.scripts if s not in self.scripts ])
        if hasattr(component, 'scriptage'):
            self.scriptage = self.scriptage + component.scriptage
        if hasattr(component, 'template_vars'):
            self.template_vars.update(component.template_vars)
        self.append(component)
        return self

    def show_errors(self, *errs):
        for msg in errs:
            flask.flash(msg)
        
    @property
    def response(self):
        for component in self:
            if hasattr(component, 'redirect'):
                return component.redirect
        for idx,css in enumerate(self.css):
            if not css.startswith("http"):
                self.css[idx] = url_for('static', filename=css)
        for idx,script in enumerate(self.scripts):
            if not script.startswith("http"):
                self.scripts[idx] = url_for('static', filename=script)
        return flask.render_template("page.html", **self.template_vars)

    def show_form(self, form):
        self.script_sources.append(form)
        form.validate_on_submit()
        if form.response:
            if isinstance(form.response, dict):
                self.redirect(
                    form.response.pop('url', flask.request.url), 
                    **form.response)
            else: #Allow for form to specify a raw string to be returned
                  #This will override the normal html response
                self.redirection = form.response
        else:
            if hasattr(form, 'scripts'):
                self.scripts.extend(form.scripts)
            
            with self.content:
                form.html
        return self.response

    def show_table(self, table):
        self.script_sources.append(table)
        self.content.add(table)
        return self.response

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


class CatalogEditPage(MannaPage):
    def __init__(self, catalog):
        super().__init__(f"Edit Catalog")
        self.add_series_to(catalog)
        self.import_series_to(catalog)
        self.sync_with_vimeo(catalog)
        self.reset_to_vimeo(catalog)

    def add_series_to(self, catalog):
        add_form = self.integrate(mannatags.AddSeriesForm(catalog))
        if add_form.id in flask.request.form:
            try:
                series = catalog.sync_new(add_form.name, "TODO: Describe me")
                self.redirect(flask.request.url, 
                              to_form=add_form, 
                              with_msg="Added series {series.name}")
            except Exception as e:
                emsg = str(e) + traceback.format_exc()
                flask.flash(f"Failed to create series: {emsg}")

    def import_series_to(self, catalog):
        import_form = self.integrate(mannatags.ImportSeriesForm(catalog))
        if import_form.id in flask.request.form:
            series = catalog.import_series(
                eval(import_form.serselect),
                datetime.strptime(import_form.postdate, "%Y-%m-%d"))
            self.redirect(flask.request.url, 
                          to_form=import_form,
                          with_msg=f"Imported {series.name}")

    def sync_with_vimeo(self, catalog):
        sync_form = self.integrate(mannatags.SyncWithVimeoForm(catalog))
        if sync_form.id in flask.request.form:
            flask.flash(executor.monitor(catalog.sync_gen))

    def reset_to_vimeo(self, catalog):
        reset_form = self.integrate(mannatags.ResetToVimeoForm(catalog))
        if reset_form.id in flask.request.form:
            #catalog._drop_all()
            flask.flash("Disabled for now...must be performed manually.")


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


class VideoEditPage(MannaPage):
    def __init__(self, video):
        super().__init__(video)
        purge_form = self.integrate(mannatags.PurgeVideoForm(video))
        self.on_ready.append(f"""
            $('#{purge_form.id}').click( 
                    function () {{ 
                        return confirm('Purge video: {video.name} ?') 
                    }} ); """)
        if purge_form.id in flask.request.form:
            video.delete()
            self.redirect('/', with_msg=f"Video {video.name} purged from catalog")


class VideoSetPage(MannaPage):
    _vidTableTag = mannatags.VideoTable
    def __init__(self, name, vids, **kwargs):
        super().__init__(name)
        self.videos = vids
        self.vtable = self.integrate(self._vidTableTag(vids, **kwargs))


class LatestVideosPage(VideoSetPage):
    _vidTableTag = mannatags.LatestVideoTable


class SeriesPage(VideoSetPage):
    def __init__(self, series):
        super().__init__(f"{series.name} Series", series.videos, pageLength=25)


class SeriesEditPage(VideoSetPage):
    def __init__(self, series):
        super().__init__(f"Edit {series.name} Series", series.videos)
        self.upload_to(series)
        self.sync(series)
        self.delete(series)
        self.redate(series)
        self.rename(series)
        self.normalize(series)
        self.commit(series)

    def upload_to(self, series):
        upform = self.integrate(mannatags.UploadForm(series, 2))
        if upform.id in flask.request.form:
            vidurls = flask.request.form.getlist('vidids')
            postdates = flask.request.form.getlist('postdates')
            msg = []
            for vidid, postdate in zip(vidurls, postdates):
                resp, vid = series.add_video(vidid, vidate=postdate)
                if resp.ok:
                    with self.vtable.body:
                        self.vtable._make_table_row(vid)
                    msg.append(
                        f"Uploaded {vid.name} to {series.name} " 
                        + "with post date" 
                        + f"{vid.date.strftime('%Y-%m-%d')}...")
                else:
                    msg.append(f"Failed upload: {resp}")
            self.redirect(flask.request.url, with_msg=msg)

    def sync(self, series):
        sync_form = self.integrate(mannatags.SyncSeriesForm(series))
        if sync_form.id in flask.request.form:
            series.sync_with_vimeo()
            self.redirect(
                flask.request.url, 
                with_msg=f"Syncronizing {series.name} with vimeo...")

    def delete(self, series):
        del_form = self.integrate(mannatags.DeleteSeriesForm(series))
        if del_form.id in flask.request.form:
            try:
                series.delete()
                self.redirect('/', with_msg=f"Removed {series.name}!")
            except Exception as e:
                self.redirect(
                    flask.request.url, 
                    with_msg=f"Failed removing {series.name}: {e}")
            
    def redate(self, series):
        redate_form = self.integrate(mannatags.RedateSeriesForm(series))
        if redate_form.id in flask.request.form:
            sdate = datetime.fromisoformat(redate_form.start_date)
            vindicies = flask.request.form['selection']
            if vindicies:
                vindicies = eval(vindicies)
                if isinstance(vindicies, int):
                    vindicies = [ vindicies ]
                vids = [ series.videos[v] for v in vindicies ]
            else:
                vids = series.videos
            sort_col, sort_dir = flask.request.form['order'].split(',')
            def sort_on(obj):
                sidx = int(sort_col)
                if sidx == 1:
                    obj = obj.series
                sort_attr = "create_date name duration".split()[int(sort_col)-1]
                return getattr(obj, sort_attr)
            vids = sorted(vids, key=sort_on, reverse=(sort_dir == 'desc'))
            date_inc = int(flask.request.form['date_inc'])
            vid_set = int(flask.request.form['vid_set'])
            series.upDateVids(sdate, vids, date_inc, vid_set)
            self.redirect(
                flask.request.url, 
                with_msg=f"Redated one or more videos from {series.name}")

    def rename(self, series):
        rename_form = self.integrate(mannatags.RenameSeriesForm(series))
        if rename_form.id in flask.request.form:
            if rename_form.new_series_name: 
                series.name = rename_form.new_series_name
                series.save()
            return self.response

    def normalize(self, series):
        normalize_form = self.integrate(mannatags.NormalizeSeries(series))
        if normalize_form.id in flask.request.form:
            for vid in series.normalizable_vids:
                vid.name = series.normalized_name(vid.name)
                vid.save()
            self.redirect(
                flask.request.url, 
                with_msg=f"Normalized names in {series.name}")

    def commit(self, series):
        commit_form = self.integrate(mannatags.CommitSeries(series))
        if commit_form.id in flask.request.form:
            for vid in series.videos:
                vid.commit_meta()


class ErrorPage(MannaPage):
    def __init__(self, err):
        super().__init__("Trouble in Paradise...")
        with self.content:
            tags.h2(err)
