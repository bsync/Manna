import os
import dominate.tags as tags
import datetime
import flask
from flask import url_for

g50c50 = "display: grid; grid-template-columns: 50% 50%; "
g30c70 = "display: grid; grid-template-columns: 30% 70%; "
g100 = "display: grid; grid-template-columns: 100%; "

class SubmissionForm(tags.form):
    tagname = "form"

    def __new__(cls, *args, **kwargs):
        """Disabling tag decorator logic"""
        return object.__new__(cls)

    def __init__(self, title, **kwargs):    
        super().__init__(id=self.id, method=self.method, **kwargs)
        with self.add(tags.fieldset()):
            tags.legend(title)
            self.content=tags.div()
            tags.input(name=f"{self.id}", type='hidden')
            tags.input(_class='selection', name='selection', type='hidden')
            tags.input(_class='order', name='order', type='hidden')
            self.submit_tag = tags.input(id=f"{self.submit_id}", 
                                         type='submit', 
                                         _class='submit_button',
                                         value=self.submission_label, 
                                         style="clear: both; width: 100%; "
                                              +"margin-top: 20px;")
    @property
    def submit_id(self):
        return f"{self.id}_Submit"

    def __getattr__(self, name):
        if name in flask.request.form:
            return flask.request.form[name]
        else:
            raise AttributeError(f"{self} has no attribute {name}")

    @property
    def id(self):
        return self.__class__.__name__

    @property
    def method(self):
        return "POST"

    @property
    def submission_label(self):
        return self.__class__.__name__.replace("Form", "")


class UploadForm(SubmissionForm):
    def __init__(self, series, cnt=1, **kwargs):    
        super().__init__(f"Add upto {cnt} new videos to \"{series.name}\"")
        with self.content:
            tags.input(id="accessToken", type="hidden", 
                       value=f"{os.getenv('VIMEO_TOKEN')}")
            with tags.div(id="upbox", **{"data-maxcnt":"2"}):
                with tags.div(_class="upunit", style=g30c70):
                    tags.label("Video Name:") 
                    tags.input(_class="vidname", type="text",
                               value=series.videos[-1].next_name)
                    tags.label("Video Author:") 
                    tags.input(_class="vid_author", type="text", 
                               name="vid_author", value="Pastor")
                    tags.label("Video File:") 
                    tags.input(_class="fileselect", type="file",)
                    tags.label("Video Date:") 
                    tags.input(_class="post_date", type="date", 
                               name="postdates", 
                               value=f"{datetime.date.today().isoformat()}")
                    tags.label("Upload Progress:") 
                    tags.div(_class="progress")
                    tags.label("Status:") 
                    tags.div(_class="status")
                    tags.input(_class="vidid", name="vidids", type="hidden") 
            tags.button(" + ", cls="add_field", style="display: inline-block;")
            tags.button(" - ", cls="del_field", style="display: inline-block;")

    @property
    def scripturls(self):
        return [ url_for('static', filename="vimeo-upload.js"),
                 url_for('static', filename="manna-upload.js") ] 
                 

class SyncSeriesForm(SubmissionForm):
    def __init__(self, series, **kwargs):    
        super().__init__(f"Sync {series.name} with vimeo")
        with self.content:
            tags.p("""Resynchronize this series with the source content
                      from the backing store (vimeo, etc...)""",
                    style="text-align: left;")


class DeleteSeriesForm(SubmissionForm):
    def __init__(self, series, **kwargs):    
        super().__init__(f"Remove the {series.name} series")
        self.series = series
        with self.content:
            tags.p("""Remove the series from the Manna app.

                        Note this does NOT remove the series from the backing
                        storage. So if vimeo is your backing store for example,
                        you will still need to remove the series from vimeo
                        separately but the series will no longer be represented
                        in the Manna app unless it is reimported.""",
                    style="text-align: left;")

    @property
    def on_ready_scriptage(self):
        return f"""$('#{self.id}').click(
                function () {{ return confirm('{self.series.name}?') }} ); """

class RedateSeriesForm(SubmissionForm):
    def __init__(self, series, **kwargs):    
        super().__init__(f"Redate the {series.name} series")
        with self.content:
            with tags.div(style=g50c50 + "text-align: left;"):
                tags.label("Apply the following start date from the top down:")
                tags.input(name='start_date', type='date', 
                           value=f"{datetime.date.today().isoformat()}")


class RenameSeriesForm(SubmissionForm):
    def __init__(self, series, **kwargs):    
        super().__init__(f"Rename the {series.name} series")
        with self.content:
            tags.attr(style=g50c50)
            tags.label("New series name:")
            tags.input(name="new_series_name", type='text')


class NormalizeSeries(SubmissionForm):
    def __init__(self, series, **kwargs):    
        super().__init__(f"Normalize the video names in {series.name}")
        with self.content:
            if series.normalizable_vids:
                tags.label("The following video titles can be normalized:")
                self.ntable = VideoTable(series.normalizable_vids)
                example = series.normalizable_vids[0].name
                tags.pre(f'For example, "{example}" would become ' +
                         f'"{series.normalized_name(example)}"', 
                        style="text-align: left;")
            else:
                tags.p("Nothing to normalize in this series...")
                self.submit_tag['disabled']=True
                    
    @property
    def on_ready_scriptage(self):
        return self.ntable.on_ready_scriptage


class AddSeriesForm(SubmissionForm):
    "Add a new series to the catalog"
    def __init__(self, catalog, **kwargs):    
        super().__init__("Add a new series")
        with self.content:
            tags.attr(style=g30c70)
            tags.label("Series Name:")
            tags.input(name='name')
            #tags.label("Description:")
            #tags.textarea(form=f"{self.id}", name='description')


class ImportSeriesForm(SubmissionForm):
    #passwd = wtf.PasswordField("Password", default='(auto generate)') 
    def __init__(self, catalog, **kwargs):    
        super().__init__("Import a series to the Catalog")
        # Form list from the unlisted series of the catalog
        # That is a list of vimeo folders that are not
        # present as a VideoSeries object in mongodb
        us = list(catalog.unlisted_series())
        # get the names associated with the vimeo folders
        usn = [ x['name'] for x in us ]
        # Stringify the unlisted series dictionary data because both name and
        # data elements of the SelectField choice list
        us = [ str(x) for x in us ]
        with self.content:
            tags.attr(style=g30c70)
            tags.label("Choose from existing vimeo folders: ")
            with tags.select(name="serselect", type='text'):
                for opt, name in zip(usn, us):
                    tags.option(opt, value=name)
            tags.label("First recorded:")
            tags.input(_class="post_date", type="date", 
                       name="postdate", 
                       value=f"{datetime.date.today().isoformat()}")


class SyncWithVimeoForm(SubmissionForm):
    def __init__(self, catalog, **kwargs):    
        super().__init__("Resync catalog with vimeo")


class ResetToVimeoForm(SubmissionForm):
    def __init__(self, catalog, **kwargs):    
        super().__init__("Reset catalog with vimeo")


class PurgeVideoForm(SubmissionForm):
    "Purge video from catalog (but NOT from vimeo)"
    def __init__(self, video, **kwargs):    
        super().__init__(f"Purge {video.name} from {video.series.name} series")


class FileSelector(tags.input):
    tagname = "input"
    def __init__(self, *args, **kwargs):    
        super().__init__(*args, type='file', **kwargs)


class DataTableTag(tags.table):
    tagname = 'table'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, id=f"{self.table_id}", style="width: 100%;")
        self.head = self.add(tags.thead()) 
        self.body = self.add(tags.tbody())
        self.dtargs = 'order:[[0,"desc"]], select:{"items": "row"} '  \
                    + ",".join([ f' {x}: {y}' for x,y in kwargs.items() ])

    _tblcnt = 0
    @property
    def table_id(self):
        if not hasattr(self, 'tblnum'):
            self.tblnum = DataTableTag._tblcnt
            DataTableTag._tblcnt += 1
        return f"{self.__class__.__name__}_table{self.tblnum}"

    @property
    def on_ready_scriptage(self):
        return f"""
            var table = $('#{self.table_id}').DataTable({{{self.dtargs}}});
            $(".submit_button").click(function() {{
                $(".selection").val(table.rows( {{ selected: true }} )[0])
                $(".order").val(table.order()[0]) }}); """

    def __new__(_cls, *args, **kwargs):
        # Disable base class tag decoration logic which is otherwise being
        # inadvertently triggered by singular callable args such as are 
        # typically used by subclasses of DataTableTag and which tend to pass
        # arguments like mongo queryset results which are callable...
        return object.__new__(_cls)


class SeriesTable(DataTableTag):
    def __init__(self, catalog, **kwargs):
        super().__init__(**kwargs)
        with self.head:
            tags.th("Date", _class="dt-head-left")
            tags.th("Series", _class="dt-head-left")
            tags.th("Lesson Count", _class="dt-head-left")
        with self.body:
            @tags.tr
            def _row(x):
                tags.td(str(x.create_date))
                tags.td(tags.a(x.name, 
                               href=url_for('.show_series_page', series=x.name),
                               onclick="shift_edit(event, this)"))
                tags.td(f"{len(x.videos)}")
            for x in catalog: 
                _row(x)


class VideoTable(DataTableTag):
    play_endpoint='.play_restricted'
    def __init__(self, vids, *args, **kwargs):
        super().__init__(*args,  **kwargs)
        with self.head:
            tags.th("Date", _class="dt-head-left")
            tags.th("Series", _class="dt-head-left")
            tags.th("Lesson", _class="dt-head-left")
            tags.th("Duration", _class="dt-head-left")
        with self.body:
            if len(vids) == 0:
                tags.h3("No connection to videos, try again later...")
            else: 
                for vid in vids: 
                    try:
                        if vid in vid.series.videos:
                            self._make_table_row(vid)
                    except Exception as e:
                        print(f"Removing {vid.name} because: {e}")
                        vid.delete()

    def _make_table_row(self, vid):
        with tags.tr():
            try:
                tags.attr()
                tags.td(str(vid.create_date))
                tags.td(vid.series.name) 
                tags.td(
                    tags.a(vid.name, 
                       href=url_for(self.play_endpoint,
                                    series=vid.series.name,
                                    video=vid.name),
                       onclick="shift_edit(event, this)"))
                tags.td(f"{int(vid.duration/60)} mins")
            except Exception as e:
                print(f"Removing corrupt video {vid.name}!")
                vid.delete()

class LatestVideoTable(VideoTable):
    play_endpoint='.play_latest'

