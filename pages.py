import flask, os
import vimongo, forms
import dominate
import dominate.tags as tags
from dominate.util import raw
from urllib.parse import quote
from flask_executor import Executor

ex = Executor()

def init_app(app):
    ex.init_app(app)
    vimongo.init_app(app)
    Page.title = app.config.get("title", Page.title)


class Page(dominate.document):
    title = "Manna"

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

        with self.body.add(tags.div(cls="container")):
            self.header = tags.div(id="header")
            with self.header.add(tags.h2()):
                tags.a(self.title, href='/', id="title")
                tags.h3(self.subtitle, id="subtitle")
                tags.h4(f"{self.status}", id="status", style="display: none;") 
            self.controls = tags.div(id="controls")
            self.content = tags.div(id="content")
            self.footer = tags.div(id="footer")
            with self.footer:
                tags.a("Latest", href=flask.url_for(".latest"))
                tags.a("Back to the Front", href="/")
                tags.a("Catalog", href=flask.url_for(".catalog"), 
                        onclick="edit(event, this)")

    @property
    def status(self):
        return vimongo.db.status

    @property
    def _scriptage(self):
        return f""" function sync_status() {{ 
                $('#status').show()
                $.ajax({{url: window.location.href + '/status', 
                         success:  function(data) {{ $('#status').html(data); }},
                         complete: function() {{ 
                                var status = $('#status').text()
                                if (status.startsWith('redirect:')) {{
                                    window.location.href=status.split(':')[1]; 
                                }} else if (status != 'ready') {{ 
                                    setTimeout(sync_status, 1000); 
                                }}
                            }}
                        }})}} 

                function edit(event, slink) {{ 
                    var link = '\manna'
                    if (event.shiftKey)
                        lref = slink.href.replace(link, link+'\/edit');
                        lref = lref.replace('/latest/', '/');
                        window.location.href = lref;
                        return true; }} 
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
            scriptage = f"$(document).ready( function() {{ {scriptage} }})" 
        self.jscript(scriptage)

    def datatable(self, table_id, **options):
        cdnbase = "https://cdn.datatables.net/1.10.20"
        with self.head:
            self.csslink(f"{cdnbase}/css/jquery.dataTables.css")
            self.csslink(flask.url_for('.static', filename="tables.css"))
            self.jquery(f"$('#{table_id}').DataTable({options})")
            self.scriptfiles(f"{cdnbase}/js/jquery.dataTables.js")
        return tags.table(id=f"{table_id}")

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
        return form


class PasswordPage(Page):

    def __init__(self, target):
        super().__init__("Authorization Required")
        self.passForm = self.integrate(forms.PasswordForm(target))

    @property
    def passes(self):
        return self.passForm.passes


class ErrorPage(Page):

    def __init__(self, err):
        super().__init__("Trouble in Paradise...")

        with self.content:
            str(err.description)


class LatestPage(Page):

    def __init__(self, count=10):
        super().__init__(f"Latest {count} Lessons")
        vids = vimongo.Video.latest(count)
        with self.content:
            with self.datatable("latest_table", order=[[0,"desc"]]): 
                with tags.thead():
                    tags.th("Date", _class="dt-head-left")
                    tags.th("Series", _class="dt-head-left")
                    tags.th("Name", _class="dt-head-left")
                    tags.th("Duration", _class="dt-head-left")
                with tags.tbody():
                    if len(vids) == 0:
                        tags.h3("No Connection to Videos, try again later...")
                    else: 
                        for vid in vids: 
                            self._make_vid_row(vid)

    def _make_vid_row(self, vid):
        with tags.tr():
            try:
                tags.attr()
                tags.td(str(vid.create_date))
                vurl = quote(f"latest/albums/{vid.album.name}/videos/{vid.name}")
                tags.td(
                    tags.a(vid.album.name, 
                           href=quote(f"albums/{vid.album.name}"),
                           onclick="edit(event, this)"))
                tags.td(tags.a(vid.name, href=vurl, onclick="edit(event, this)"))
                tags.td(f"{int(vid.duration/60)} mins")
            except Exception as e:
                print(f"Removing corrupt video {vid.name} from mongoDB!")
                vid.delete()


class CatalogPage(Page):

    def __init__(self, subtitle="Series Catalog"):
        super().__init__(subtitle)
        with self.content:
            with self.datatable("album_table", order=[[0,"desc"]]):
                with tags.thead():
                    tags.th("Date", _class="dt-head-left")
                    tags.th("Series", _class="dt-head-left")
                    tags.th("Lesson Count", _class="dt-head-left")
                with tags.tbody():
                    @tags.tr
                    def _row(x):
                        tags.td(str(x.create_date))
                        tags.td(tags.a(x.name, 
                                href=quote(f"/manna/albums/{x.name}"),
                                onclick="edit(event, this)"))
                        tags.td(f"{len(x.videos)}")
                    for x in vimongo.VideoSeries.objects: _row(x)
        

class CatalogEditorPage(CatalogPage):

    def __init__(self):
        super().__init__("Series Catalog Editor")
        self.integrate(forms.AddSeriesForm(vimongo.VideoSeries))
        scf = self.integrate(forms.SyncWithVimeoForm("Sync Catalog with Vimeo"))
        if scf.validate():
            self.jquery("sync_status()")
            ex.submit(vimongo.VideoSeries.sync_all)


class SeriesPage(Page):

    def __init__(self, alb):
        super().__init__(f"Lessons of {alb}")
        album = vimongo.VideoSeries.named(alb)
        with self.content:
            if album.html:
                raw(album.html)
                

class SeriesEditorPage(SeriesPage):

    def __init__(self, alb):
        super().__init__(alb)
        album = vimongo.VideoSeries.named(alb)
        self.integrate(forms.AddVideosForm(album))
        sav = self.integrate(forms.SyncWithVimeoForm(f"Sync {alb} with vimeo"))
        self.integrate(forms.DeleteSeriesForm(album))

        if sav.validate():
            self.jquery("sync_status()")
            ex.submit(album.synchronize)


class VideoPlayer(Page):

    def __init__(self, alb, vid=None):
        super().__init__(f"{vid} of {alb}" if vid else f"{alb}")
        album = vimongo.VideoSeries.named(alb)
        with self.content:
            if vid:
                video = album.get_video_named(vid)
                tags.div(raw(video.html), id="player")
                tags.a("click to play audio?",
                       href=flask.url_for('.audio_response', 
                                          album=album.name, 
                                          audio=video.name))
            else:
                tags.div(raw(album.html), id="player")


class VideoEditor(VideoPlayer):

    def __init__(self, album, vid):
        super().__init__(album, vid)
        album = vimongo.VideoSeries.named(album)
        video = album.get_video_named(vid)
        self.integrate(forms.PurgeVideoForm(video))


class AudioPage(Page):

    def __init__(self, alb, vid):
        super().__init__(f"Audio for Lesson {vid} of album {alb}")

    def generate_mp3(self):
        yield 'This feature is coming soon!'

    @property
    def response(self):
        return flask.Response(self.generate_mp3(), mimetype="text/plain")

