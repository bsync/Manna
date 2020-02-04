import flask, os
import dominate as dom
import dominate.tags as tags
import forms
from dominate.util import raw
from urllib.parse import quote, unquote

class Page(dom.document):

    def __new__(_cls, *args, **kwargs):
        "Disables decorators from this subclass onward."
        return object.__new__(_cls)

    def __init__(self, title):
        doc = super().__init__(title)
        with self.head:
            for css in [ "Page.css", f"{type(self).__name__}.css" ]:
                if os.path.exists(f"static/{css}"):
                    tags.link(rel="stylesheet", type="text/css", 
                              href=flask.url_for('static', filename=css))
            tags.script(""" function edit(event, slink) { 
                    if (event.shiftKey)
                        window.location.href = slink.href.concat('/edit')
                    return true; 
                } """)

    def use_table(self, table_id, **options):
        with self.head:
            tags.script(crossorigin="anonymous",
                        src="https://code.jquery.com/jquery-3.4.1.slim.min.js")
            cdnbase = f"https://cdn.datatables.net/1.10.20"
            tags.link(rel="stylesheet", type="text/css", 
                      href=cdnbase + "/css/jquery.dataTables.css")
            tags.link(rel="stylesheet", type="text/css", 
                      href=flask.url_for('static', filename="tables.css"))
            tags.script(type="text/javascript", charset="utf8",
                        src=cdnbase + "/js/jquery.dataTables.js")
            tags.script("$(document).ready( function () { "
               + f"$('#{table_id}').DataTable({options});" + "});",
                        type="text/javascript")

    @tags.div
    def banner(self, subtitle):
        tags.attr(cls="banner")
        tags.h2(tags.a("Tullahoma Bible Church", href="/joomla")) 
        tags.h3(subtitle) 

    @property
    def container(self):
        return self.body.add(tags.div(cls="row-container"))

    @tags.div
    def footer(self):
        tags.attr(cls="footer")
        tags.a("Latest", href="/manna")
        tags.a("Back to the Front", href="/joomla")
        tags.a("Catalog", href="/manna/albums", onclick="edit(event, this)")


class LatestLessons(Page):
    def __init__(self, vids):
        super().__init__("Lessons")
        self.use_table("latest_table", order=[[0,"desc"]])
        with self.container:
            self.banner("Latest Lessons")
            with tags.table(id="latest_table"):
                with tags.thead():
                    tags.th("Date", _class="dt-head-left")
                    tags.th("Name", _class="dt-head-left")
                    tags.th("Album", _class="dt-head-left")
                    tags.th("Duration", _class="dt-head-left")
                with tags.tbody():
                    if len(vids) == 0:
                        tags.h3("No Connection to Videos, try again later...")
                    else: 
                        for x in vids: 
                            with tags.tr():
                                tags.attr()
                                tags.td(str(x.create_date))
                                vurl = quote(f"latest/{x.vimid}")
                                tags.td(tags.a(x.name, href=vurl))
                                aurl = quote(f"albums/{x.album.name}")
                                tags.td(tags.a(x.album.name, href=aurl))
                                tags.td(f"{int(x.duration/60)} mins")
            self.footer()


class VideoPlayer(Page):
    def __init__(self, vid):
        super().__init__(f"Lesson {vid.name} of {vid.album.name}")
        with self.container:
            self.banner(f"{vid.name} of {vid.album.name}")
            tags.div(raw(vid.html))
            tags.div(
                tags.a("click to play audio?",
                        href="/manna/albums/{album.name}/audios/{vid.name}"))
            self.footer()

class FormPage(Page):
    def __init__(self, form):
        super().__init__(form.title)
        self.form = form

    @property
    def hasValidSubmission(self):    
        return self.form.validate_on_submit()


class PasswordPage(FormPage):
    def __init__(self, target):
        super().__init__(forms.PasswordForm(
                'Provide password to access "'
                + f'{unquote(os.path.split(target)[-1])}"'))
        with self.container:
            self.banner("Authorization Required")
            with self.form.as_dom_tag:
                tags.br()
                tags.p(f"{self.error}")
            self.footer()
        self.target = target

    @property
    def guess(self):    
        return self.form.data['guessword']

    @property
    def error(self):
        "TODO: Report errors!"
        return ""


class Album(Page):
    def __init__(self, alb):
        super().__init__(f"Lessons of {alb.name}")
        with self.container: 
            self.banner(f"{alb.name}")
            raw(alb.html)
            self.footer()


class Catalog(FormPage):
    def __init__(self, series, edit=False):
        super().__init__(forms.CatalogEditor())
        self.use_table("album_table")
        with self.container:
            self.banner("Series Catalog")
            if edit:
                tags.div(self.form.as_dom_tag)
            tags.div(id="status")
            with tags.table(id="album_table"):
                with tags.thead():
                    tags.th("Date", _class="dt-head-left")
                    tags.th("Album", _class="dt-head-left")
                    tags.th("Lesson Count", _class="dt-head-left")
                with tags.tbody():
                    @tags.tr
                    def _row(x):
                        tags.td(str(x.create_date))
                        tags.td(tags.a(x.name, 
                                href=quote(f"/manna/albums/{x.name}"),
                                onclick="edit(event, this)"))
                        tags.td(f"{len(x.videos)}")
                    for x in series: _row(x)
            self.footer()
    
    @property
    def status(self):
        return self.getElementById('status')
        
    @status.setter
    def status(self, value):
        self.getElementById('status').add(value)


class ErrorPage(Page):
    def __init__(self, err):
        super().__init__("Error")
        with self.container: 
            self.banner("Trouble in Paradise...")
            tags.div(str(err))
            self.footer()

