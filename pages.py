import sys, traceback, os
import flask
import dominate, dominate.tags as tags
import executor, forms
from login import login_user
from datetime import datetime, timedelta, timezone
from dominate.util import raw
from urllib.parse import unquote
from pathlib import Path

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
        self.scriptfiles(flask.url_for('.static', filename="jquery.fitvids.js"))
        self.jquery("""$('#content').fitVids();""")
        if len(executor.futures):
            if executor.futures.done(executor.fk):
                executor.futures.pop(executor.fk)
                print(f"Finished with {executor.fk}")
            else:
                self.head.add(tags.meta(http_equiv="refresh", content="1"))
        with self.body.add(tags.div(cls="container")):
            self.header = tags.div(id="header")
            with self.header.add(tags.h2()):
                tags.a(self.title, href='/', id="title")
                tags.h3(self.subtitle, id="subtitle")
                self.status
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
        with tags.div(id="status") as sdiv:
            self._page_status = tags.h4(id="pstatus", style="display: none;")
            tags.h4(executor.status, id="estatus", 
                    style="display: none;" if executor.status == 'idle' else "")
        return sdiv

    @status.setter
    def status(self, value):
        self._page_status['style']=""
        self._page_status.children.append(value)

    @property
    def _scriptage(self):
        return f""" function check_edit(event, slink) {{ 
                    var pre = slink.pathname.split('/')[1];
                    if (event.shiftKey)
                        event.preventDefault();
                        lref = slink.href.replace(pre, pre+'\/edit');
                        lref = lref.replace('/latest/', '/');
                        window.location.href = lref;
                        return false; }} """
    
    @property
    def response(self):
        "Returns the a response as the page itself"
        return str(self)

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
            scriptage = f"""$(document).ready( function() {{ {scriptage} }})"""
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
                        tags.h3("No Connection to Videos, try again later...")
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
            2)  augmenting the page head with any raw javascript or jquery
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

    def monitor(self, func):
        fname = func.__name__
        if fname not in executor.futures:
            def watcher(yielder):
                for status in yielder():
                    print(f"{fname} yielded {status}")
                    executor.status = status
            executor.submit_stored(fname, watcher, func)
            self.head.add(tags.meta(http_equiv="refresh", content="1"))
            executor.fk = fname

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
                        title=x.name,
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
            tags.div(
                raw(vid.html), 
                tags.div(
                    tags.a(tags.button("Play Audio"),
                           target='apframes',
                           href=flask.url_for('.play_audio', 
                                              series=vid.series.name, 
                                              video=vid.name)),
                    tags.iframe(name="apframes", src="", frameBorder="0"),
                    tags.a(tags.button("Download Video"), 
                           href=vid.dlink),
                    id="options"),
                id="player")
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
        elif self.SyncWithVimeoForm.was_submitted:
            self.monitor(catalog.sync_gen)
        elif self.ResetToVimeoForm.was_submitted:
            catalog._drop_all()
            self.monitor(catalog.sync_gen)
        return self.show_catalog(catalog.objects())

    def show_series(series):
        self.video_table(series.videos)
        return self.response

    def edit_series(self, series):
        self.integrate(forms.AddVideosForm(self.series))
        self.integrate(forms.SyncWithVimeoForm(f"Sync {alb} with vimeo"))
        self.integrate(forms.DeleteSeriesForm(f"Delete empty {alb} series"))
        self.jquery(f"""
            $('#{self.DeleteSeriesForm.submitField.id}').click(
                function () {{ 
                    return confirm("Delete series: {self.series.name} ?") 
                                }} ) """)
        self.integrate(forms.DateSeriesForm(f"Modify {alb} start Date"))

        if self.AddVideosForm.was_submitted:
            self.AddVideosForm.initiate_upload( 
                alb.upload_action(
                    self.AddVideosForm.vidName.data, 
                    self.AddVideosForm.vidDesc.data, 
                    flask.request.url
                    )
                )
        elif self.AddVideosForm.finished_upload:
            self.monitor(self.series.add_new, self.AddVideosForm.uploaded_uri)
        elif self.DeleteSeriesForm.was_submitted:
            import pdb; pdb.set_trace()
            try:
                self.series.remove()
                self.status = f"Deleted {self.series.name}"
                return self.redirect(".catalog")
            except Exception as e:
                self.status = f"Failed deleting {self.series.name}: {e}"
        elif self.SyncWithVimeoForm.was_submitted:
            self.series.update()
            self.status = f"Sync {self.series.name} with vimeo"
        elif self.DateSeriesForm.was_submitted:
            sdate = self.DateSeriesForm.data['recordedDate']
            for vid in self.series.videos:
                vid.create_date = sdate
                sdate += timedelta(days=3)
                vid.save()
            self.status = f"Redated {self.series.name} starting at {sdate}"
        return self.response

    def edit_video(self, video):
        self.integrate(forms.PurgeVideoForm(video))
        if self.PurgeVideoForm.was_submitted:
            self.jquery(
                f"""$('#{self.submitField.id}').click( 
                        function () {{ 
                            return confirm("Purge video: {video.name} ?") 
                        }} )""")
            self.status = f"Video {video.name} purged from catalog"
            video.delete()
            self.vid.series.sync_vids()
            return self.redirect(".latest")
        return self.response

    def play_audio(self, video):
        def generate_mp3():
            import subprocess as sp
            ffin = f' -i "{video.vlink}" '
            ffopts = " -af silenceremove=1:1:.01 -ac 1 -ab 64k -ar 44100 -f mp3 "
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
