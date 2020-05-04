import sys, os, re
import flask, requests
import dominate, dominate.tags as tags
import executor, mongo, forms
from login import login_user
from datetime import datetime, timedelta, timezone
from dominate.util import raw
from urllib.parse import quote, unquote
from pathlib import Path

def init_flask(app):
    executor.init_flask(app)
    mongo.init_flask(app)
    Page.title = app.config.get("title", Page.title)
    return sys.modules[__name__] #Basically just use this module as the page manager

class Page(dominate.document):
    title = "Tullahoma Bible Church"
    def __new__(_cls, *args, **kwargs):
        "Disables decorators from this subclass onward."
        return object.__new__(_cls)
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
        style_str="display: none;" if self.status.startswith('done') else ""
        with self.body.add(tags.div(cls="container")):
            self.header = tags.div(id="header")
            with self.header.add(tags.h2()):
                tags.a(self.title, href='/', id="title")
                tags.h3(self.subtitle, id="subtitle")
                tags.h4(self.status, id="status", style=style_str)
            self.controls = tags.div(id="controls")
            self.content = tags.div(id="content")
            self.footer = tags.div(id="footer")
            with self.footer:
                tags.a("Latest", href=flask.url_for(".latest"))
                tags.a("Back to the Front", href="/")
                tags.a("Catalog", href=flask.url_for(".catalog"), 
                        onclick="check_edit(event, this)")

    @property
    def status(self):
        msgs = " ".join(flask.get_flashed_messages()) 
        if len(msgs):
            if not executor.status.startswith('done'):
                msgs += executor.status
        else:
            msgs = executor.status
        return msgs

    @property
    def _scriptage(self):
        return f""" function check_edit(event, slink) {{ 
                    var pre = slink.pathname.split('/')[1];
                    if (event.shiftKey)
                        event.preventDefault();
                        lref = slink.href.replace(pre, pre+'\/edit');
                        lref = lref.replace('/latest/', '/');
                        window.location.href = lref;
                        return false; }} 
        """
    
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
                print(f"Removing corrupt video {vid.name} from mongoDB!")
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


class AuthenticationPage(Page):
    def __init__(self, target):
        super().__init__("Authorization Required")
        self.integrate(forms.PasswordForm(target))

    @property
    def response(self):
        if self.PasswordForm.passes:
            login_user()
            tbase = Path(self.PasswordForm.target).name
            flask.session[unquote(tbase)]=True
            return flask.redirect(self.PasswordForm.target)
        return str(self)


class ErrorPage(Page):
    def __init__(self, err):
        super().__init__("Trouble in Paradise...")

        with self.content:
            str(err.description)


class LatestPage(Page):
    def __init__(self, count=10):
        super().__init__(f"Latest {count} Lessons")
        self.vids = mongo.Video.latest(count)
        with self.content:
            self.video_table(self.vids, order=[[0,"desc"]])


    @property
    def feed(self):
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
                    for i,x in enumerate(self.vids) ],)
        return flask.jsonify(rfeed)
        #roku_sc = mongo.ShowCase.named('Roku')
        #roku_sc.replace_videos(self.vids)
        #roku = requests.get(
        #        "https://vimeo.com/showcase/7028576/feed/roku/bd4c2f777e")
        #rokmovs = roku.json()['movies']
        #for vid, content in zip(self.vids, rokmovs):
        #    content['title']=vid.series.name
        #roku = flask.Response(rfeed, mimetype='application/json')


class CatalogPage(Page):
    def __init__(self, subtitle="Series Catalog"):
        super().__init__(subtitle)
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
                                       href=flask.url_for('.series_page', 
                                                          series=x.name),
                                       onclick="check_edit(event, this)"))
                        tags.td(f"{len(x.videos)}")
                    for x in mongo.VideoSeries.objects(): 
                        _row(x)
        

class CatalogEditorPage(CatalogPage):
    def __init__(self):
        super().__init__("Series Catalog Editor")
        self.integrate(forms.AddSeriesForm("Add a series to the Catalog"))
        self.integrate(forms.SyncWithVimeoForm("Sync Catalog with Vimeo"))
        self.integrate(forms.ResetToVimeoForm("Reset Catalog to Vimeo"))

    @property
    def response(self):
        if self.SyncWithVimeoForm.was_submitted:
            self.monitor(mongo.VideoSeries.sync_gen)
        elif self.ResetToVimeoForm.was_submitted:
            mongo.VideoSeries._drop_all()
            self.monitor(mongo.VideoSeries.sync_gen)
        elif self.AddSeriesForm.was_submitted:
            name = self.AddSeriesForm.seriesName.data
            description = self.AddSeriesForm.seriesDesc.data
            try:
                mongo.VideoSeries.add_new(name, description)
                flask.flash(f"Added series {unquote(name)}")
                return self.redirect(".catalog")
            except Exception as e:
                flask.flash(f"Failed to create series: {str(e)}")
        return str(self)


class SeriesPage(Page):
    def __init__(self, alb):
        super().__init__(f"Lessons of {alb}")
        series = mongo.VideoSeries.named(alb)
        with self.content:
            self.video_table(series.videos)
            #if series.html:
            #    raw(series.html)
                

class SeriesEditorPage(SeriesPage):
    def __init__(self, alb):
        super().__init__(alb)
        self.series = mongo.VideoSeries.named(alb)
        self.integrate(forms.AddVideosForm(self.series))
        self.integrate(forms.SyncWithVimeoForm(f"Sync {alb} with vimeo"))
        self.integrate(forms.DeleteSeriesForm(f"Delete empty {alb} series"))
        self.integrate(forms.DateSeriesForm(f"Modify {alb} start Date"))
        self.upload_uri = flask.request.args.get('video_uri', False)

    @property
    def response(self):
        if self.upload_uri:
            if executor.status.startswith("Waiting"): 
                self.monitor(self.series.add_new, self.upload_uri)
        elif self.DeleteSeriesForm.was_submitted:
            try:
                self.jquery(
                f"""
                $('#{self.DeleteSeriesForm.submitField.id}').click(
                    function () {{ 
                        return confirm("Delete series: {self.series.name} ?") 
                                    }} ) """)
                self.series.remove()
                flask.flash(f"Deleted {unquote(self.series.name)}")
                return self.redirect(".catalog")
            except Exception as e:
                flask.flash(
                   f"Failed deleting {unquote(self.series.name)}: {e}")
        elif self.SyncWithVimeoForm.was_submitted:
            self.series.update()
            flask.flash(f"Sync {self.series.name} with vimeo")
        elif self.DateSeriesForm.was_submitted:
            sdate = self.DateSeriesForm.data['recordedDate']
            for vid in self.series.videos:
                vid.create_date = sdate
                sdate += timedelta(days=3)
                vid.save()
            flask.flash(f"Redated {self.series.name} starting at {sdate}")
        return str(self)


class VideoPlayer(Page):
    def __init__(self, alb, vid=None):
        super().__init__(f"{vid} of {alb}" if vid else f"{alb}")
        series = mongo.VideoSeries.named(alb)
        with self.content:
            if vid:
                video = series.video_named(vid)
                tags.div(
                    raw(video.html), 
                    tags.div(
                        tags.a(tags.button("Play Audio"),
                               href=flask.url_for('.audio_response', 
                                                  series=series.name, 
                                                  audio=video.name)),
                        tags.a(tags.button("Download Video"), 
                               href=video.dlink),
                        id="options"),
                    id="player")
            else:
                tags.div(raw(series.html), id="player")


class VideoEditor(VideoPlayer):
    def __init__(self, series, vid):
        super().__init__(series, vid)
        self.series = mongo.VideoSeries.named(series)
        self.video = self.series.video_named(vid)
        self.integrate(forms.PurgeVideoForm(self.video))

    @property
    def response(self):
        if self.PurgeVideoForm.was_submitted:
            self.jquery(
                f"""$('#{self.submitField.id}').click( 
                        function () {{ 
                            return confirm("Purge video: {self.video.name} ?") 
                        }} )""")
            flask.flash(f"Video {self.video.name} purged from catalog")
            self.video.delete()
            self.series.sync_vids()
            return self.redirect(".latest")
        return str(self)


class AudioPage(Page):
    def __init__(self, alb, vid):
        super().__init__(f"Audio for Lesson {vid} of series {alb}")
        self.series = mongo.VideoSeries.named(alb)
        self.video = self.series.video_named(vid)

    def generate_mp3(self):
        import subprocess as sp
        ffin = f' -i "{self.video.vlink}" '
        ffopts = " -af silenceremove=1:1:.01 -ac 1 -ab 64k -ar 44100 -f mp3 "
        ffout = ' - '
        ffmpeg = 'ffmpeg' + ffin + ffopts + ffout
        tffmpeg = "timeout -s SIGKILL 300 " + ffmpeg 
        with sp.Popen(tffmpeg, shell=True,
                      stdout = sp.PIPE, stderr=sp.PIPE,
                      close_fds = True, preexec_fn=os.setsid) as process:
            while process.poll() is None:
                yield process.stdout.read(1000)

    @property
    def response(self):
        return flask.Response(self.generate_mp3(), mimetype="audio/mpeg")

