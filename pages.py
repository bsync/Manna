import flask, os
import dominate as dom
import dominate.tags as tags
import forms
from dominate.util import raw
from urllib.parse import quote


class Page(dom.document):

    def __new__(_cls, *args, **kwargs):
        "Disables decorators from this subclass onward."
        return object.__new__(_cls)

    def __init__(self, subtitle):
        doc = super().__init__(subtitle)
        with self.head:
            for css in [ "Page.css", f"{type(self).__name__}.css" ]:
                if os.path.exists(f"static/{css}"):
                    tags.link(rel="stylesheet", type="text/css", 
                              href=flask.url_for('static', filename=css))
            tags.script(""" function edit(event, slink) { 
                    if (event.shiftKey)
                        window.location.href = 
                            slink.href.replace('\/manna\/', '\/manna\/edit\/')
                    return true; 
                } """)

        self.grid = self.body.add(tags.div(id="topgrid", cls="container"))
        self.header = self.grid.add(tags.div(id="header"))
        self.header.add(tags.h2(tags.a("Tullahoma Bible Church", href="/joomla"))) 
        self.status = self.header.add(tags.div(id="status"))
        self.subtitle = self.header.add(tags.h3(subtitle, id="subtitle"))
        self.content = self.grid.add(tags.div(id="content"))
        self.controls = self.content.add(tags.div(id="controls"))
        self.footer = self.grid.add(tags.div(id="footer"))
        with self.footer:
            tags.a("Latest", href="/manna")
            tags.a("Back to the Front", href="/joomla")
            tags.a("Catalog", href="/manna/albums", onclick="edit(event, this)")
        self.status.add(flask.get_flashed_messages())
        self.forms=[]
           
    @property
    def response(self):
        "Returns the first form with a response or the page itself."
        for form in self.forms:
            if form.response:
                return flask.redirect(form.response)
        return str(self)

    def csslink(self, cssfile):
        if cssfile not in self.head:
            return tags.link(rel="stylesheet", type="text/css", href=cssfile)

    def scriptfiles(self, *urls):
        for url in urls:
            if url not in str(self.head):
                self.head.add(tags.script(crossorigin="anonymous", src=url))

    def jscript(self, scriptage):
        return tags.script(raw(scriptage), type="text/javascript")

    def jquery(self, scriptage, on_ready=True):
        self.scriptfiles("https://code.jquery.com/jquery-3.4.1.min.js")
        if on_ready:
            scriptage = f"$(document).ready( function() {{ {scriptage} }})" 
        return self.jscript(scriptage)

    def datatable(self, table_id, **options):
        cdnbase = "https://cdn.datatables.net/1.10.20"
        with self.head:
            self.csslink(f"{cdnbase}/css/jquery.dataTables.css")
            self.csslink(flask.url_for('static', filename="tables.css"))
            self.jquery(f"$('#{table_id}').DataTable({options})")
            self.scriptfiles(f"{cdnbase}/js/jquery.dataTables.js")
        return tags.table(id=f"{table_id}")

    def integrateForm(self, form, container=None):
        """Integrates the given form into the page using container

            Integration means: 
            
            1)  augmenting the page head to source any external scriptfiles
                associated with the form,
            2)  augmenting the page head with any raw javascript or jquery
                scriptage associated with the form, 
            3)  merging the DOM content of the form itself into the given
                container which defaults to the Page's internal content
                element,
            4)  and finally, associating the form with the Page instance as
                an accessible attribute. The attribute name is formed from the
                form's type name by lower casing the first letter of that type
                name. So, for example, integrating a form of type PasswordForm
                will result in a new 'passwordForm' attribute on the Page. 
        """
        self.forms.append(form)
        if container is None: container = self.content
        with self.head: #Augment page's head content
            if hasattr(form, 'scriptage'):
                self.jscript(f"{form.scriptage}")
            if hasattr(form, 'qscriptage'):
                self.jquery(f"{form.qscriptage}")
            if hasattr(form, 'scriptfiles'):
                self.scriptfiles(*form.scriptfiles)
        container.add(form.content) #Merge DOM content
        formTypeName = type(form).__name__
        formTypeName = formTypeName[0].lower() + formTypeName[1:]
        setattr(self, formTypeName, form) #Store form as an attribute of page
        

class CatalogPage(Page):
    def __init__(self, catalog, title="Series Catalog"):
        super().__init__(title)
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
                    for x in catalog.objects: _row(x)
    

class CatalogEditorPage(CatalogPage):
    def __init__(self, catalog, title="Catalog Editor"):
        super().__init__(catalog, title)
        with self.head:
            self.jquery("""function vSync() {
                $.ajax({ url: '/manna/vsync/status', 
                         success: function(data) { $('#sync').html(data); },
                         complete: function() { 
                            if( $('#sync').text() != 'Done' ) { 
                                setTimeout(vSync, 5000)}}})}""")
        with self.controls as ctls:
            self.integrateForm(forms.AddSeriesForm(catalog), ctls)
            #self.integrateForm(forms.SyncToVimeoForm(catalog), ecg)


class LatestLessonsPage(Page):
    def __init__(self, vids):
        super().__init__("Latest Lessons")
        with self.content:
            with self.datatable("latest_table", order=[[0,"desc"]]):
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
                                tags.td(tags.a(x.name, href=vurl,
                                               onclick="edit(event, this)"))
                                aurl = quote(f"albums/{x.album.name}")
                                tags.td(tags.a(x.album.name, href=aurl,
                                               onclick="edit(event, this)"))
                                tags.td(f"{int(x.duration/60)} mins")


class SeriesPage(Page):
    def __init__(self, alb):
        super().__init__(f"Lessons of {alb.name}")
        with self.content:
            if alb.html:
                raw(alb.html)


class SeriesEditorPage(SeriesPage):
    def __init__(self, alb):
        super().__init__(alb)
        with self.controls as ctls:
           self.integrateForm(forms.AddVideosForm(alb), ctls)
           self.integrateForm(forms.SyncToVimeoForm(alb), ctls)
           self.integrateForm(forms.DeleteSeriesForm(alb), ctls)


class VideoPlayer(Page):
    def __init__(self, vid):
        super().__init__(f"{vid.name} of {vid.album.name}")
        with self.content:
            tags.div(raw(vid.html))
            tags.a("click to play audio?",
                   href="/manna/albums/{album.name}/audios/{vid.name}")


class VideoEditor(VideoPlayer):
    def __init__(self, vid):
        super().__init__(vid)
        with self.controls as ctls:
           self.integrateForm(forms.PurgeVideoForm(vid), ctls)


class PasswordPage(Page):
    def __init__(self, target):
        super().__init__("Authorization Required")
        self.integrateForm(forms.PasswordForm(target))

    @property
    def passes(self):
        return self.passwordForm.passes


class ErrorPage(Page):
    def __init__(self, err):
        super().__init__("Trouble in Paradise...")
        self.content.add(tags.div(str(err)))

