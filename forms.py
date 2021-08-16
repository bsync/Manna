import flask, os, sys, datetime, traceback, re
import wtforms.fields as fields
import wtforms.validators as validators
import dominate.tags as tags
from dominate.util import raw
from flask_wtf import FlaskForm
from login import Login
from tables import VideoTable

class Forms(object):
    def __new__(cls, app, store):
        global mstore, login
        mstore = store
        login = Login(app)
        return sys.modules[__name__] #just use this module as the page manager

class MannaForm(FlaskForm):
    _submit = "Manna Form"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response = None
        self.submittable = True

    _tid = 0
    @property
    def newid(self):
        MannaForm._tid += 1
        return MannaForm._tid

    @property
    def html(self):
        with tags.div(cls="manna_form row") as form_html:
            with tags.form(cls="col", id=f"{self._submit}_form", method="POST"):
                raw(str(self.csrf_token(id=self.newid)))
                with tags.div(cls="row"):
                    self.populate_form(tags.div(cls="form-group"))
                    tags.input(type='hidden', name="form_name", value=f"{self._submit}_form")
                    submit=tags.input(type='submit', id=self._submit, value=self._submit)
                    if not self.submittable:
                        submit['disabled']=True
                    tags.div("Results: ", id=f"{self._submit}_form_results")
        return form_html

    def validate_on_submit(self):
        wtf_validate = super().validate_on_submit() 
        multiform_validate = f"{self._submit}_form" == flask.request.form.get('form_name', '')
        if wtf_validate and multiform_validate:
            try:
                self.on_validated()
            except Exception as e:
                emsg = str(e) + traceback.format_exc()
                flask.flash(f"Operation failed for {self}: {emsg}")
    
    def populate_form(self, atag):
        pass

    def on_validated(self):
        pass

    def redirect(self, **kwargs):
        self.response = kwargs

    def __getattr__(self, name):
        if name in flask.request.form:
            return flask.request.form['name']
        else:
            raise AttributeError(f"{name} not found in {self}")


class AddSeriesToCatalogForm(MannaForm):
    _submit = "Add a series to the catalog:"
    series_name = fields.StringField("Name the Series", [validators.InputRequired()])

    def populate_form(self, atag):
        with atag:
            raw(str(self.series_name.label(for_="series_name")))
            raw(self.series_name(id="series_name", cls="form-control"))
        return atag
    
    def on_validated(self):    
        aseries = mstore.add_new_series(self.series_name.data, "TODO: Describe me")
        self.redirect(with_msg=f"Added series {aseries.name}")


class SyncWithCatalogForm(MannaForm):
    _submit = "Sync entire catalog with backing store:"

    def on_validated(self):    
        mstore.clear_cache()
        self.redirect(with_msg=f"Cached series have been refreshed...")


class SeriesForm(MannaForm):
    _submit = "Series Form:"
    table_options = { 'pageLength':5 }

    def __init__(self, series, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.series = series
        tbopts = dict(pageLength=5)
        tbopts.update(self.table_options)
        self.table = VideoTable(series.videos(), **tbopts)

    @property
    def on_ready(self):
        return self.table.on_ready

class AddVideoForm(SeriesForm):
    _submit = "Add Video"
    video_name = fields.StringField("Video Name:", [validators.InputRequired()])
    video_author = fields.StringField("Presented by:", [validators.InputRequired()])
    video_file = fields.FileField("Video File:", [validators.InputRequired()])
    video_date = fields.DateField("Video Date:", [validators.InputRequired()])
    series_name = fields.HiddenField("series name")
    series_uri = fields.HiddenField("series uri")
    vid_id = fields.HiddenField("uploaded video ids")

    def populate_form(self, atag, nextvidname):
        def render_input(name, typ="Text", cls="", val=''):
            newid = self.newid
            tags.label(name, for_=newid)
            tags.input(name=name, id=newid, type=typ, 
                       cls=f"form-control {cls}", value=val)
        with atag:
            with tags.div(id="upbox"):
                with tags.div(cls="upunit"):
                    render_input("Video Name:", cls="vidname", val=nextvidname)
                    render_input("Author Name:", val="Pastor")
                    render_input("File:", typ="File", cls="fileselect")
                    render_input("Date:", typ="Date", cls="post_date",
                                 val=f"{datetime.date.today().isoformat()}")
                    tags.label("Upload Progress:") 
                    tags.div(cls="progress")
                    tags.div(cls="status")
                    raw(self.series_name(id=self.newid, class_="seriesname", value=self.series.name))
                    raw(self.series_uri(id=self.newid, class_="seriesuri", value=self.series.uri))
                    raw(self.vid_id(id=self.newid, class_="vid_id"))
                    tags.button(" + ", cls="add_field", style="display: inline-block;")
                    tags.button(" - ", cls="del_field", style="display: inline-block;")
        return atag


class AddVideoSetForm(SeriesForm):
    _submit = "Add Videos"
    access_token = fields.HiddenField("vimeo access")

    def __init__(self, series, cnt=1, *args, **kwargs):
        super().__init__(series, *args, **kwargs)
        self.vidups = [ AddVideoForm(series, *args, **kwargs) ] * cnt

    @property
    def scripts(self):
        return [ flask.url_for('static', filename="vimeo-upload.js"),
                 flask.url_for('static', filename="manna-upload.js") ] 

    def populate_form(self, atag):
        atag.add(raw(self.access_token(id="accessToken", value=f"{os.getenv('VIMEO_TOKEN')}")))
        vname = self.series.next_vid_name
        for idx,vidup in enumerate(self.vidups, 1):
            vidpop = vidup.populate_form(tags.div(f"Upload #{idx}", cls="addvid_form"), vname)
            vname = re.sub("(.*)(\d+)", lambda x: x.group(1) + str(int(x.group(2))+1), vname)
            if idx == 1:
                delbutton = vidpop.get('button', cls="del_field")[0]
                delbutton.set_attribute('style', "display: none;")
            else:
                vidpop.set_attribute('style', "display: none;")
            atag.add(vidpop)
        addButton = vidpop.get('button', cls="add_field")[0]
        addButton.set_attribute('style', "display: none;")
        atag.add(self.table)
        return atag

    def on_validated(self):    
        vidids = [ vid for vid in flask.request.form.getlist('vid_id') if vid ]
        self.series.add_videos(*vidids)
        vidnames = flask.request.form.getlist('Video Name:')[:len(vidids)]
        self.redirect(with_msg=f"Added {vidnames} to {self.series.name}", 
                      watchTranscode=",".join(vidids))


class PurgeVideoFromSeries(SeriesForm):
    _submit = "Purge_Video"
    vidlist = fields.SelectField("Choose a video to purge:") 
    table_options = { 'select':{ 'style':'single'} }

    def __init__(self, series, *args, **kwargs):
        super().__init__(series, *args, **kwargs)
        self.vidlist.choices = [ v.name for v in series.videos() ]

    @property
    def on_ready(self):
        return super().on_ready + f"""
          $('#{self._submit}').click(
            function(evt) {{ 
                evt.preventDefault()
                vc = {self.table.id}.rows('.selected').data()
                $.ajax({{url: escape(`videos/${vc[0][2]}/edit`)+`?purge`, 
                         async: false,
                         success: function(result) {{ 
                           $('#Purge_Video').html(result) }} }})
            }})"""

    def populate_form(self, atag):
        atag.add(self.table)
        #with atag:
        #    raw(str(self.vidlist.label(for_="choiceList")))
        #    raw(self.vidlist(id="choiceList"))
        return atag

    def on_validated(self):    
        video = self.series.video_by_name(self.vidlist.data)
        resp = self.series.purge_video(video)
        if resp.status_code != 204:
            flask.flash(resp.text)
        self.redirect(with_msg=f"Purged {self.vidlist.data}")


class SyncWithSeriesForm(SeriesForm):
    _submit = "Sync Videos"

    def on_validated(self):    
        self.series.source.clear_cache()
        self.redirect(with_msg=f"Resynced series {self.series.name}.")

    def populate_form(self, atag):
        atag.add(self.table)
        return atag

class NormalizeSeries(SeriesForm):
    _submit = "Normalize Titles"

    def populate_form(self, atag):
        with atag:
            if self.series.normalizable_vids:
                tags.label("The following video titles can be normalized:")
                example = self.series.normalizable_vids[0].name
                tags.pre(f'For example, "{example}" would become ' +
                         f'"{self.series.normalized_name(example)}"', 
                        style="text-align: left;")
            else:
                tags.p("Nothing to normalize in this series...")
                self.submittable = False
        return atag

    def on_validated(self):    
        for vid in self.series.normalizable_vids:
            vid.save(name=self.series.normalized_name(vid.name))
        self.series.source.clear_cache()
        self.redirect(with_msg=f"TODO: Normalize series {self.series.name}.")


class RedateSeriesForm(SeriesForm):
    _submit = "RedateVideos"
    table_options = { 'select':{ 'style':'multi'} }

    @property
    def scripts(self):
        return [ flask.url_for('static', filename="redate.js"),
                 flask.url_for('static', filename="date.format.js") ]

    @property
    def on_ready(self):
        return super().on_ready + f"""
          $('#vid_set').spinner({{step: 1, min: 1, max: 3}})
          $('#date_inc').spinner({{step: 1, min: 1, max: 3}})

          set_redate_strategy('row', {self.table.id})

          function changing_selection(e,dt,type,idxs) {{ 
                set_redate_strategy(type,dt) 
          }}
          {self.table.id}.on('select', changing_selection)
          {self.table.id}.on('deselect', changing_selection)

          $('#{self._submit}').click(
            function(evt) {{ 
                redate_vids(evt, {self.table.id})
            }})"""
    

    def populate_form(self, atag):    
        with atag.add(self.table):
            tags.p( "Starting from ",
                    tags.input(name='start_date', type='date', id="start_date",
                               value=f"{datetime.date.today().isoformat()}"),
                    " and increasing by ",
                    tags.input(type="text", id="date_inc", name="date_inc", size="3", value=3),
                    " days for every ",
                    tags.input(type="text", id="vid_set", name="vid_set", size="3", value=2),
                    " videos, ",
                    tags.label("", id="strategy"))


