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

    def __init__(self, subtitle):
        doc = super().__init__(subtitle)
        self.ext_hash={}
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

        self.grid = self.body.add(tags.div(id="topgrid", cls="container"))
        self.header = self.grid.add(tags.div(id="header"))
        self.header.add(tags.h2(tags.a("Tullahoma Bible Church", href="/joomla"))) 
        self.subtitle = self.header.add(tags.h3(subtitle, id="subtitle"))
        self.content = self.grid.add(tags.div(id="content"))
        self.footer = self.grid.add(tags.div(id="footer"))
        with self.footer:
            tags.a("Latest", href="/manna")
            tags.a("Back to the Front", href="/joomla")
            tags.a("Catalog", href="/manna/albums", onclick="edit(event, this)")
           
    def csslink(self, *cssfiles):
        with self.head:
            for cssfile in cssfiles:
                if cssfile not in self.ext_hash:
                    tags.link(rel="stylesheet", type="text/css", href=cssfile)
                    self.ext_hash[cssfile]=True

    def jscript(self, scriptage, *jsfiles):
        with self.head:
            for jsfile in jsfiles:
                if jsfile not in self.ext_hash:
                    tags.script(crossorigin="anonymous", src=jsfile)
                    self.ext_hash[jsfile]=True
            tags.script(raw(scriptage), type="text/javascript")

    def jquery(self, qscriptage, *jsfiles):
        self.jscript(qscriptage, 
                    "https://code.jquery.com/jquery-3.4.1.min.js", 
                    *jsfiles)

    def use_table(self, table_id, **options):
        cdnbase = "https://cdn.datatables.net/1.10.20"
        self.csslink(f"{cdnbase}/css/jquery.dataTables.css",
                     flask.url_for('static', filename="tables.css"))
        self.jquery(f"""$(document).ready( function() {{ 
                            $('#{table_id}').DataTable({options}); }})""",
                    f"{cdnbase}/js/jquery.dataTables.js")

    def addDomForm(self, form):
        if hasattr(form, 'scriptage'):
            self.jscript(form.scriptage)
        if hasattr(form, 'qscriptage'):
            self.jquery(form.qscriptage)
        self.content.add(form.content)
        fname = form.__class__.__name__
        fname = fname[0].lower() + fname[1:]
        setattr(self, fname, form)


class Catalog(Page):
    def __init__(self, series, edit=False):
        super().__init__("Series Catalog")
        self.use_table("album_table", order=[[0,"desc"]])
        if edit:
            self.addDomForm(forms.EditCatalogForm(series))
        with self.content:
            with tags.table(id="album_table"):
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
                    for x in series.objects: _row(x)
    

class LatestLessons(Page):
    def __init__(self, vids):
        super().__init__("Latest Lessons")
        self.use_table("latest_table", order=[[0,"desc"]])
        with self.content:
            with tags.table(id="latest_table"):
                with tags.thead():
                    tags.th("Date", _class="dt-head-left")
                    tags.th("Name", _class="dt-head-left")
                    tags.th("Series", _class="dt-head-left")
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
                                tags.td(tags.a(x.album.name, href=aurl,
                                               onclick="edit(event, this)"))
                                tags.td(f"{int(x.duration/60)} mins")


class Series(Page):
    def __init__(self, alb, edit=False):
        super().__init__(f"Lessons of {alb.name}")
        if edit:
            self.addDomForm(forms.SeriesForm(alb))

        if alb.html:
            self.content.add(raw(alb.html))


class VideoPlayer(Page):
    def __init__(self, vid):
        super().__init__(f"{vid.name} of {vid.album.name}")
        with self.content:
            tags.div(raw(vid.html))
            tags.a("click to play audio?",
                   href="/manna/albums/{album.name}/audios/{vid.name}")


class PasswordPage(Page):
    def __init__(self, target):
        super().__init__("Authorization Required")
        self.addDomForm(forms.PasswordForm(target))
        self.target=target

    @property
    def passes(self):    
        try:
            import passcheck
            if self.passwordForm.validate_on_submit():
                return passcheck(self.target, self.passwordForm.data['guessword'])
            else:
                return False
        except Exception as e:
            return True


class ErrorPage(Page):
    def __init__(self, err):
        super().__init__("Trouble in Paradise...")
        self.content.add(tags.div(str(err)))

