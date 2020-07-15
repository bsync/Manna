import sys, traceback, os, re
import flask, html
import dominate, dominate.tags as tags
import executor, forms
from login import login_user
from datetime import datetime, timezone
from dominate.util import raw
from urllib.parse import unquote
from pathlib import Path
from requests.models import PreparedRequest

def init_flask(app):
    executor.init_flask(app)
    MannaPage.title = app.config.get("TITLE", MannaPage.title)
    if app.env == "development":
        MannaPage.title = MannaPage.title + " (dev) "
    return sys.modules[__name__] #just use this module as the page manager

class MannaPage(dominate.document):
    title = "Tullahoma Bible Church"
    def __init__(self, subtitle=''):
        super().__init__(self.title)
        self.subtitle = subtitle if subtitle else self.__class__.__name__
        with self.head:
            for css in [ "Page.css", f"{type(self).__name__}.css" ]:
                if os.path.exists(f"static/{css}"):
                    tags.link(rel="stylesheet", type="text/css", 
                              href=flask.url_for('.static', filename=css))
        self.jquery(self._scriptage, on_ready=False)
        self.scriptfiles(
            flask.url_for('.static', filename="jquery.fitvids.js"))
        self.jquery("""$('#content').fitVids();""")
        with self.body.add(tags.div(cls="container")):
            self.header = tags.div(id="header")
            with self.header.add(tags.h2()):
                tags.a(self.title, href='/', id="title")
                tags.h3(self.subtitle, id="subtitle")
                tags.h4(id="status", style="display: none;")
            self.controls = tags.div(id="controls")
            self.content = tags.div(id="content")
            self.footer = tags.div(id="footer")
            with self.footer:
                tags.a("Latest", href=flask.url_for(".latest"))
                tags.a("Back to the Front", href="/")
                tags.a("Catalog", href=flask.url_for(".show_catalog_page"), 
                        onclick="check_edit(event, this)")

    @property
    def status(self):
        return self.getElementById('status').children[0]

    @status.setter
    def status(self, value):
        statel = self.getElementById('status')
        statel.children.append(value)
        statel['style'] = ''

    @property
    def url(self):
        return getattr(self, '_url', flask.request.url)

    @url.setter
    def url(self, value):
        self._url = value

    @property
    def _scriptage(self):
        return f""" function check_edit(event, slink) {{ 
                    if (event.shiftKey)
                        event.preventDefault();
                        lref = slink.href + '\/edit';
                        lref = lref.replace('/latest/', '/');
                        window.location.href = lref;
                        return false; }} """
    
    def csslink(self, cssfile):
        if cssfile not in str(self.head):
            return tags.link(rel="stylesheet", type="text/css", href=cssfile)

    def scriptfiles(self, *urls):
        for url in urls:
            if url not in str(self.head):
                self.head.add(tags.script(crossorigin="anonymous", src=url))

    def jscript(self, scriptage):
        self.head.add(tags.script(f"{scriptage}"))

    def jquery(self, scriptage, on_ready=True):
        self.scriptfiles("https://code.jquery.com/jquery-3.4.1.min.js")
        if on_ready:
            scriptage = f"$(document).ready( function() {{ {scriptage} }})"
        self.jscript(scriptage)

    def datatable(self, **options):
        cdnbase = "https://cdn.datatables.net/1.10.20"
        table_id = f"{self.__class__.__name__}_table"
        with self.head:
            self.csslink(f"{cdnbase}/css/jquery.dataTables.css")
            self.csslink(flask.url_for('.static', filename="tables.css"))
            self.jquery(f"$('#{table_id}').DataTable({options})")
            self.scriptfiles(f"{cdnbase}/js/jquery.dataTables.js")
        return tags.table(id=f"{table_id}")

    def video_table(self, vids, **kwargs):
        with self.content:
            with self.datatable(**kwargs): 
                with tags.thead():
                    tags.th("Date", _class="dt-head-left")
                    tags.th("Series", _class="dt-head-left")
                    tags.th("Lesson", _class="dt-head-left")
                    tags.th("Duration", _class="dt-head-left")
                with tags.tbody():
                    if len(vids) == 0:
                        tags.h3("No connection to videos, try again later...")
                    else: 
                        for vid in vids: 
                            try:
                                if vid in vid.series.videos:
                                    self.make_table_row(vid)
                            except Exception as e:
                                print(f"Removing {vid.name} because: {e}")
                                vid.delete()
        return self.response

    def make_table_row(self, vid):
        with tags.tr():
            try:
                tags.attr()
                tags.td(str(vid.create_date))
                tags.td(vid.series.name) 
                tags.td(tags.a(vid.name, 
                               href=flask.url_for('.latest_player', 
                                                  series=vid.series.name,
                                                  video=vid.name),
                               onclick="check_edit(event, this)"))
                tags.td(f"{int(vid.duration/60)} mins")
            except Exception as e:
                print(f"Removing corrupt video {vid.name}!")
                vid.delete()

    def integrate(self, form, container=None):
        """Integrates the given form into the page using container

            Integration means: 

            1)  augmenting the page head to source any external scriptfiles
                associated with the form,
        5   2)  augmenting the page head with any raw javascript or jquery
                scriptage associated with the form, 
            3)  merging the DOM content of the form itself into the given
                container which defaults to the Page's internal content
                element,
        """
        with self.head: #Augment page's head content
            if hasattr(form, 'scriptage'):
                self.jscript(f"{form.scriptage}")
            if hasattr(form, 'qscriptage'):
                self.jquery(f"{form.qscriptage}")
            if hasattr(form, 'scriptfiles'):
                self.scriptfiles(*form.scriptfiles)
        if container is None: container = self.controls
        container.add(form.content) 
        setattr(self, form.__class__.__name__, form)
        return form

    def redirect(self, url, **kwargs):
        return flask.redirect(flask.url_for(url, **kwargs))

    def roku_feed(self, vids):
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
                    for i,x in enumerate(vids) ],)
        return flask.jsonify(rfeed)

    def play_video(self, vid):
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
                       href=flask.url_for('.play_audio', 
                                          series=vid.series.name, 
                                          video=vid.name)),
                tags.a(tags.button("Download Audio"),
                       href=flask.url_for('.play_audio', 
                                          series=vid.series.name, 
                                          video=vid.name),
                                          download=vid.name),
                tags.a(tags.button(f"Play {altdisp} Video"), 
                       href=flask.url_for('.latest_player', 
                                          series=vid.series.name, 
                                          video=vid.name,
                                          quality=altqual)),
                tags.a(tags.button("Download Video"), href=vid.dlink),)
        return self.response

    def play_series(self, series):
        with self.content:
            tags.div(raw(series.html), id="player")
        return self.response

    def show_catalog(self, catalog):
        with self.content:
            with self.datatable(order=[[0,"desc"]]):
                with tags.thead():
                    tags.th("Date", _class="dt-head-left")
                    tags.th("Series", _class="dt-head-left")
                    tags.th("Lesson Count", _class="dt-head-left")
                with tags.tbody():
                    @tags.tr
                    def _row(x):
                        tags.td(str(x.create_date))
                        tags.td(tags.a(x.name, 
                                       href=flask.url_for('.show_series_page', 
                                                          series=x.name),
                                       onclick="check_edit(event, this)"))
                        tags.td(f"{len(x.videos)}")
                    for x in catalog: 
                        _row(x)
        return self.response

    def edit_catalog(self, catalog):
        self.integrate(forms.AddSeriesForm("Add a series to the Catalog"))
        self.integrate(forms.ImportSeriesForm(catalog))
        self.integrate(forms.SyncWithVimeoForm("Sync Catalog with Vimeo"))
        self.integrate(forms.ResetToVimeoForm("Reset Catalog to Vimeo"))
        if self.AddSeriesForm.was_submitted:
            try:
                catalog.sync_new(
                        self.AddSeriesForm.name, 
                        self.AddSeriesForm.description)
                self.status = f"Added series {self.AddSeriesForm.name}"
            except Exception as e:
                emsg = str(e) + traceback.format_exc()
                self.status = f"Failed to create series: {emsg}"
        elif self.ImportSeriesForm.was_submitted:
            series = catalog.import_series(
                eval(self.ImportSeriesForm.seriesSelect.data),
                self.ImportSeriesForm.seriesDate,
                self.ImportSeriesForm.passwd)
            self.status = f"Imported {series.name}"
        elif self.SyncWithVimeoForm.was_submitted:
            self.status = executor.monitor(catalog.sync_gen)
        elif self.ResetToVimeoForm.was_submitted:
            #catalog._drop_all()
            #self.status = executor.monitor(catalog.sync_gen)
            self.status = "Disabled for now...this must be performed manually."
        return self.show_catalog(catalog.objects())

    def show_series(self, series):
        self.video_table(series.videos)
        return self.response

    def edit_series(self, series):
        self.integrate(forms.AddVideosForm(series))
        self.integrate(
            forms.SyncWithVimeoForm(f"Sync {series.name} with vimeo"))
        self.integrate(forms.DeleteSeriesForm(f"Remove {series.name} series"))
        self.jquery(f"""
            $('#{self.DeleteSeriesForm.submitField.id}').click(
                function () {{ 
                    return confirm('Remove series: {series.name} ?') 
                                }} ) """)
        self.integrate(
            forms.DateSeriesForm(f"Modify {series.name} start Date"))
        if self.AddVideosForm.was_submitted:
            self.status = self.AddVideosForm.initiate_upload(series) 
        elif self.AddVideosForm.was_uploaded:
            req = PreparedRequest()
            req.prepare_url(flask.request.base_url, {'processing':True,})
            self.url = req.url
            self.status = self.AddVideosForm.process_upload(series)
        elif self.DeleteSeriesForm.was_submitted:
            try:
                series.remove()
                self.status = f"Removed {series.name}"
            except Exception as e:
                self.status = f"Failed removing {series.name}: {e}"
        elif self.SyncWithVimeoForm.was_submitted:
            series.sync_with_vimeo()
            self.status = f"Sync {series.name} with vimeo"
        elif self.DateSeriesForm.was_submitted:
            sdate = self.DateSeriesForm.data['recordedDate']
            series.upDateVids(sdate)
            self.status = f"Redated {series.name} starting at {sdate}"
        return self.response

    def edit_video(self, video):
        self.integrate(
            forms.PurgeVideoForm(
                f"Purge {video.name} from {video.series.name} series"))
        self.jquery(
            f"""$('#{self.PurgeVideoForm.submitField.id}').click( 
                    function () {{ 
                        return confirm('Purge video: {video.name} ?') 
                    }} )""")
        if self.PurgeVideoForm.was_submitted:
            self.status = f"Video {video.name} purged from catalog"
            video.delete()
            return self.redirect(".latest")
        return self.response

    def play_audio(self, video):
        def generate_mp3():
            import subprocess as sp
            ffin = f' -i "{video.vlink}" '
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

    def report_error(self, err):
        with self.content:
            str(err.description)
        return self.response

    def authenticate(self, target):
        self.integrate(forms.PasswordForm(target))
        if self.PasswordForm.passes:
            login_user()
            tbase = Path(self.PasswordForm.target).name
            flask.session[unquote(tbase)]=True
            return flask.redirect(self.PasswordForm.target)
        return self.response

    @property
    def response(self):
        "Returns the response of the page"
        if 'monitor' in executor.futures._futures:
            if executor.futures.done('monitor'):
                executor.futures.pop('monitor')
            else:
                self.status = executor.status
                self.head.add(
                    tags.meta(http_equiv="refresh", content=f"3;{self.url}"))
        return str(self)
