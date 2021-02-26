import sys, traceback, os, re
import flask, flask_login
import dominate, dominate.tags as tags
import executor, mannatags
from datetime import datetime, timezone
from dominate.util import raw
from pathlib import Path
from requests.models import PreparedRequest
from flask import url_for

def init_flask(app):
    executor.init_flask(app)
    MannaPage.site_name = app.config.get("TITLE", MannaPage.site_name)
    if app.env == "development":
        MannaPage.site_name = MannaPage.site_name + " (dev) "
    return sys.modules[__name__] #just use this module as the page manager


class MannaPage(object):
    site_name = "Manna"
    cdnbase = "https://cdn.datatables.net/v/dt/dt-1.10.22/sl-1.3.1"
    scriptage = ["""
        function shift_edit(event, slink) {{ 
            if (event.shiftKey)
                event.preventDefault();
                lref = slink.href + '\/edit';
                lref = lref.replace('/latest/', '/');
                window.location.href = lref;
                return false; }} """ ]
    status_style="color: red; background: black;"

    def __init__(self, subtitle=''):
        self.doc = dominate.document(self.site_name)
        self.subtitle = subtitle if subtitle else self.__class__.__name__
        self.on_ready_scriptage = []

        with self.doc.head:
            for css in self.cssfiles.split(): 
                self._link_css(css)
            for scripturl in self.scripturls:
                tags.script(crossorigin="anonymous", src=scripturl)
            self.script_list = tags.script().children

        with self.doc.body.add(tags.div(cls="container")):
            self.header = tags.div(id="header")
            with self.header.add(tags.h2()):
                tags.a(self.site_name, href='/', id="site_name")
                tags.h3(self.subtitle, id="subtitle")
                with tags.ul(id="status", style=self.status_style):
                    for msg in flask.get_flashed_messages():
                        tags.li(msg)
            self.content = tags.div(id="content")
            self.footer = tags.div(id="footer")
            with self.footer:
                tags.a("Latest", href=url_for("list_latest"))
                tags.a("Back to the Front", href="/")
                tags.a("Catalog", 
                       href=url_for("show_catalog_page"), 
                       onclick="shift_edit(event, this)")
                tags.a("Register", href=url_for('loginbp.new_user'))
                tags.label("")
                if flask_login.current_user.is_authenticated:
                    tags.a(f"Log out", href=url_for('loginbp.logout'))
                else:
                    tags.a(f"Login", href=url_for('loginbp.login'))

    @property
    def cssfiles(self):
        return f""" {self.cdnbase}/datatables.min.css
                    tables.css 
                    Page.css 
                    {type(self).__name__}.css
                """

    @property
    def scripturls(self):
        return [ "https://code.jquery.com/jquery-3.4.1.min.js" ,
                 url_for('static', filename="jquery.fitvids.js"),
                f"{self.cdnbase}/datatables.min.js" ]

    @property
    def html(self):
        "Late bind scriptage and return the html of the page"
        if hasattr(self, '_redirection'):
            return self._redirection

        if 'monitor' in executor.futures._futures:
            if executor.futures.done('monitor'):
                executor.futures.pop('monitor')
            else:
                flask.flash(executor.status)
                self.doc.head.add(
                    tags.meta(http_equiv="refresh", 
                              content=f"3;{flask.request.url}"))
        self.script_list.append(
            f"""$(document).ready( 
                    function() {{ 
                        {" ".join(self.on_ready_scriptage)} 
                    }}); """)
        self.script_list.extend(self.scriptage)
        return str(self.doc)

    def _link_css(self, css):
        if os.path.exists(f"static/{css}"):
            tags.link(rel="stylesheet", type="text/css", 
                      href=url_for('static', filename=css))
        elif css.startswith('http'):
            tags.link(rel="stylesheet", type="text/css", href=css)

    def integrate(self, tag, container=None):
        """Integrates the given tag into the page using container

            Integration means merging the DOM content of the tag itself into
            the given container which defaults to the Page's internal content
            element,
        """
        if container is None: container = self.content
        container.add(tags.a(name=tag.id), tag)
        with self.doc.head:
            if hasattr(tag, 'cssfiles'):
                for css in tag.cssfiles:
                    self._link_css(css)
            if hasattr(tag, 'scripturls'):
                for script in tag.scripturls:
                    tags.script(crossorigin="anonymous", src=script)
        if hasattr(tag, "scriptage"): 
            self.scriptage.append(tag.scriptage)
        if hasattr(tag, "on_ready_scriptage"): 
            self.on_ready_scriptage.append(tag.on_ready_scriptage)
        setattr(self, tag.__class__.__name__, tag)
        return tag

    def redirect(self, url, to_form=None, with_msg=False, **kwargs): 
        if to_form is not None:
            to_form = to_form.id 
            url = f"{url}#{to_form}"
        if with_msg:
            if not isinstance(with_msg, str):
                with_msg = " ".join(with_msg)
            flask.flash(with_msg, to_form)
            self.on_ready_scriptage.append(f'window.location.hash = "{to_form}"; ')
        self._redirection = flask.redirect(url, **kwargs)

    @property
    def roku(self):
        tstamp = datetime.now(tz=timezone.utc)
        tstamp = tstamp.isoformat(timespec="seconds")
        rfeed = dict(
            providerName="Pleroma Videos",
            lastUpdated=tstamp,
            language='en',
            movies=[dict(id=x.uri.split('/')[2],
                        title=f"{x.series.name}-{x.name}",
                        genres=["faith"],
                        tags=["faith"],
                        thumbnail=x.plink,
                        content=dict(
                             dateAdded=x.create_date.isoformat(),
                             duration=x.duration,
                             videos=[
                                dict(url=x.vlink, 
                                     quality="HD", 
                                     videoType="MP4"), ],
                             ),
                       releaseDate=tstamp,
                       shortDescription=x.series.name,)
                    for i,x in enumerate(self.videos) ],)
        return flask.jsonify(rfeed)


    def play_series(self, series):
        with self.content:
            tags.div(raw(series.html), id="player")
        return self.html

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
    def html(self):
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


class VideoPage(MannaPage):
    def __init__(self, vid):
        super().__init__(f"{vid.name} of {vid.series.name}")
        self.on_ready_scriptage.append("$('#content').fitVids()")
        with self.content:
            quality = flask.request.args.get('quality', 'auto')
            if quality == 'auto':
                vhtml = vid.html
                altdisp = altqual = '720p'
            else:
                tags.div(f"({quality} Version)", id="ver")
                vmatch = re.match(r'(.*src=")(\S+)(".*)', vid.html)
                vhtml = f"{vmatch.group(1)}{vmatch.group(2)}"
                vhtml = f"{vhtml}&amp;quality={quality}{vmatch.group(3)}"
                altqual = 'auto'
                altdisp = 'Hi Res'
            tags.div(
                raw(vhtml),
                tags.a(tags.button("Play Audio"),
                       href=url_for('play_audio', 
                                    series=vid.series.name, 
                                    video=vid.name)),
                tags.a(tags.button("Download Audio"),
                       href=url_for('play_audio', 
                                    series=vid.series.name, 
                                    video=vid.name),
                                    download=vid.name),
                tags.a(tags.button(f"Play {altdisp} Video"), 
                       href=url_for('play_latest', 
                                    series=vid.series.name, 
                                    video=vid.name,
                                    quality=altqual)),
                tags.a(tags.button("Download Video"), href=vid.dlink),)


class VideoEditPage(VideoPage):
    def __init__(self, video):
        super().__init__(video)
        purge_form = self.integrate(mannatags.PurgeVideoForm(video))
        self.on_ready_scriptage.append(f"""
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
                        + f"with post date {vid.create_date}...")
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
            return self.html

    def normalize(self, series):
        normalize_form = self.integrate(mannatags.NormalizeSeries(series))
        if normalize_form.id in flask.request.form:
            for vid in series.normalizable_vids:
                vid.name = series.normalized_name(vid.name)
                vid.save()
            self.redirect(
                flask.request.url, 
                with_msg=f"Normalized names in {series.name}")


class CatalogPage(MannaPage):
    def __init__(self, catalog):
        super().__init__("Catalog of Series")
        self.integrate(mannatags.SeriesTable(catalog, pageLength=25))


class ErrorPage(MannaPage):
    def __init__(self, err):
        super().__init__("Trouble in Paradise...")
        with self.content:
            tags.h2(err)
