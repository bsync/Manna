import flask, os
import dominate as dom
import dominate.tags as tags
import vimeo, forms
from dominate.util import raw
from urllib.parse import quote, unquote

class Page(dom.document):
    def __init__(self, title, table_id=None):
        doc = super().__init__(title)
        with self.head:
            for css in [ "Page.css", f"{type(self).__name__}.css" ]:
                if os.path.exists(f"static/{css}"):
                    tags.link(rel="stylesheet", type="text/css", 
                              href=flask.url_for('static', filename=css))
            if table_id:
                self._use_table(table_id, "1.10.20")

    def _use_table(self, table_id, version):
        with self.head:
            tags.script(crossorigin="anonymous",
                        src="https://code.jquery.com/jquery-3.4.1.slim.min.js")
            cdnbase = f"https://cdn.datatables.net/{version}"
            tags.link(rel="stylesheet", type="text/css", 
                      href=cdnbase + "/css/jquery.dataTables.css")
            tags.script(type="text/javascript", charset="utf8",
                        src=cdnbase + "/js/jquery.dataTables.js")
            tags.script("$(document).ready( function () { $('#"
                         + "{}".format(table_id) 
                         + "').DataTable(); } );",
                             type="text/javascript")

    @tags.div
    def banner(self, subtitle):
        tags.attr(cls="banner")
        tags.h2(tags.a("Tullahoma Bible Church", href="/joomla")) 
        tags.h3(subtitle) 

    @tags.div
    def footer(self):
        tags.attr(cls="footer")
        tags.h3(tags.a("Latest", href="/manna"))
        tags.h3(tags.a("Catalog", href="/manna/albums"))
        tags.h3(tags.a("Back to the Front", href="/joomla"))


class LatestLessons(Page):
    def __init__(self, count):
        super().__init__("Lessons", table_id="latest_table")
        with self.body.add(tags.div(cls="grid-container")):
            self.banner("Latest Lessons")
            with tags.div(cls="main"):
                self.vidTable(
                    lambda : vimeo.VideoRecord.latest(count),
                    "latest_table")
            self.footer()

    @tags.table
    def vidTable(self, vids, tbl_id):
        try: #to query vids
            tags.attr(id=tbl_id)
            with tags.thead():
                tags.th("Date", _class="dt-head-left")
                tags.th("Name", _class="dt-head-left")
                tags.th("Album", _class="dt-head-left")
                tags.th("Duration", _class="dt-head-left")
            with tags.tbody():
                for x in vids(): 
                    with tags.tr():
                        tags.attr()
                        tags.td(str(x.create_date))
                        vurl = quote(f"albums/{x.album.name}/videos/{x.name}")
                        tags.td(tags.a(x.name, href=vurl))
                        aurl = quote(f"albums/{x.album.name}")
                        tags.td(tags.a(x.album.name, href=aurl))
                        tags.td(f"{int(x.duration/60)} mins")
        except Exception as err:
            tags.div(tags.h3("No Connection to Videos, try again later..."))


class VideoPlayer(Page):
    def __init__(self, album, video):
        vid = vimeo.AlbumRecord.named(album).videoNamed(video)
        super().__init__(f"Lesson {vid.name} of {vid.album.name}")
        with self.body.add(tags.div(cls="grid-container")):
            self.banner(f"{vid.name} of {vid.album.name}")
            tags.div(raw(vid.html))
            self.footer()


class LoginPage(Page):
    def __init__(self, target):
        super().__init__("Password")
        self.target = target
        self.form = forms.PasswordForm()
        with self.body.add(tags.div(cls="grid-container")):
            tname=os.path.split(target)[-1]
            self.banner(f"Provide password to access '{unquote(tname)}'")
            with tags.form(method="POST"):
                raw(str(self.form.hidden_tag()))
                raw(f"{self.form.guessword.label} : {self.form.guessword(size=10)}")
                raw(str(self.form.submit()))
                tags.br()
                tags.p(f"{self.error}")
            self.footer()

    @property
    def guess(self):    
        return self.form.data['guessword']

    @property
    def error(self):
        "TODO: Report errors!"
        return ""

    @property
    def hasValidSubmission(self):    
        return self.form.validate_on_submit()


class Album(Page):
    def __init__(self, album):
        alb = vimeo.AlbumRecord.named(album)
        super().__init__(f"Lessons of {alb.name}")
        with self.body.add(tags.div(cls="grid-container")):
            self.banner(f"{alb.name}")
            raw(alb.html)
            self.footer()


class Catalog(Page):
    def __init__(self):
        super().__init__("Series", table_id="album_table")
        with self.body.add(tags.div(cls="grid-container")):
            self.banner("Series Catalog")
            with tags.div(cls="main"):
                self.seriesTable(lambda : vimeo.AlbumRecord.objects, "album_table")
            self.footer()

    @tags.table
    def seriesTable(self, albums, tbl_id):
        try: #to query albums
            tags.attr(id=tbl_id)
            with tags.thead():
                tags.th("Date", _class="dt-head-left")
                tags.th("Album", _class="dt-head-left")
                tags.th("Lesson Count", _class="dt-head-left")
            with tags.tbody():
                for x in albums(): 
                    with tags.tr():
                        tags.attr()
                        tags.td(str(x.create_date))
                        aurl = quote(f"albums/{x.name}")
                        tags.td(tags.a(x.name, href=aurl))
                        tags.td(f"{len(x.videos)}")
        except Exception as err:
            tags.div(tags.h3("No Connection to Series, try again later..."))
