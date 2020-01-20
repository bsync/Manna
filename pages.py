import flask
import dominate as dom
import dominate.tags as tags
import vimeo, forms
from dominate.util import raw
from urllib.parse import quote, unquote


class Page(dom.document):
    def __init__(self, title, datatable=None):
        doc = super().__init__(title)
        if datatable:
            self.use_datatable(datatable)

    def use_datatable(self, table_id, version="1.10.20"):
        with self.head:
            tags.script(src="https://code.jquery.com/jquery-3.4.1.slim.min.js",
                        integrity="sha256-pasqAKBDmFT4eHoN2ndd6lN370kFiGUFyTiUHWhU7k8=",
                        crossorigin="anonymous")
            cdnbase = "https://cdn.datatables.net/{}".format(version)
            tags.link(rel="stylesheet", type="text/css", 
                      href=cdnbase + "/css/jquery.dataTables.css")
            tags.script(type="text/javascript", charset="utf8",
                        src=cdnbase + "/js/jquery.dataTables.js")
            tags.link(rel="stylesheet", type="text/css", href="/static/data_tables.css")
            tags.script("$(document).ready( function () { $('#"
                         + "{}".format(table_id) 
                         + "').DataTable(); } );",
                         type="text/javascript")


class LatestLessons(Page):
    def __init__(self, count):
        super().__init__("Lessons", datatable="latest_table")
        with self.body:
            tags.attr(style="background-color:black; color:blue;")
            tags.h1("Pleroma Bible Church", style="text-align:center;")
            tags.h2("Latest Lessons", style="text-align:center;color:gold")
            try: #to query vimeo for latest lessons
                with tags.table(id="latest_table"):
                    with tags.thead(style="color: yellow;"):
                        tags.th("Date", _class="dt-head-left")
                        tags.th("Name", _class="dt-head-left")
                        tags.th("Album", _class="dt-head-left")
                        tags.th("Duration", _class="dt-head-left")
                    with tags.tbody():
                        for x in vimeo.VideoRecord.latest(count):
                            with tags.tr():
                                tags.attr(style="background-color:black;")
                                tags.td(str(x.create_date), style="color:gold;")
                                vurl = quote(f"albums/{x.album.name}/videos/{x.name}")
                                tags.td(tags.a(x.name, href=vurl))
                                aurl = quote(f"albums/{x.album.name}")
                                tags.td(tags.a(x.album.name, href=aurl))
                                tags.td(f"{int(x.duration/60)} mins", style="color:gold;")
            except Exception as err:
                tags.div(tags.h3("No Connection to Vimeo, try again later...", 
                                 style="text-align:center; color:red"))


class VideoPlayer(Page):
    def __init__(self, album, video):
        vid = vimeo.AlbumRecord.named(album).videoNamed(video)
        super().__init__(f"Lesson {vid.name} of {vid.album.name}")
        with self.body:
            tags.attr(style="background-color:black; color:blue; text-align: center;")
            tags.h1("Pleroma Bible Church"),
            tags.h2(f"{vid.name} of {vid.album.name}"),
            tags.div(raw(vid.html), style="display: flex; justify-content: center;")
            tags.h3(tags.a("Back to the Front", href="/manna"))


class LoginPage(Page):
    def __init__(self, target):
        super().__init__("Password")
        self.target = target
        self.form = forms.PasswordForm()
        with self.body:
            tags.attr(style="background-color:black; color:white; text-align: left;")
            tags.h1("Pleroma Bible Church")
            tags.h2(f"Provide password to access '{unquote(target)}'")
            with tags.form(method="POST"):
                raw(str(self.form.hidden_tag()))
                raw(f"{self.form.guessword.label} : {self.form.guessword(size=10)}")
                raw(str(self.form.submit()))
                tags.br()
                tags.p(f"{self.error}")
                tags.br()
                tags.a("Back to the Front", href="/manna")

    @property
    def guess(self):    
        return self.form.data['guessword']

    @property
    def error(self):
        return "TODO: Report any errors here!"

    @property
    def hasValidSubmission(self):    
        return self.form.validate_on_submit()


class Album(Page):
    def __init__(self, album):
        alb = vimeo.AlbumRecord.named(album)
        super().__init__(f"Lessons of {alb.name}")
        with self.body:
            tags.attr(style="background-color:black; color:blue; text-align: center;")
            tags.h1("Pleroma Bible Church")
            tags.h2(f"{alb.name}")
            raw(alb.html)# style="display: flex; justify-content: center;")
            tags.h3(tags.a("Back to the Front", href="/manna"))
