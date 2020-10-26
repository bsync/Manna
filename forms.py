import flask
import dominate.tags as tags
import wtforms as wtf
import executor
from flask_wtf import FlaskForm
from dominate.util import raw, text
from urllib.parse import unquote
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DateField
from requests.models import PreparedRequest
from datetime import date


@tags.fieldset
def fieldSet(name, *field_or_tags):
    if name is None: 
        container = tags.div()
    else:
        container = tags.legend(name)
    for fot in field_or_tags:
        if isinstance(fot, MannaField):
            container.add(fot.tag)
        else:
            container.add(fot)
    return container

class MannaForm(tags.form):
    tagname = "form"

    def __init__(self, title, *fields, action_url=""):
        super().__init__()
        title = title if title else self.__doc__
        fields = (*fields,  tags.input(name=title, type='submit'))
        with self.add(tags.fieldset()):
            tags.legend(title)
            for field in fields:
                field()

    @property
    def was_submitted(self):
        if self.SubmitField.name in flask.request.form:
            return self.validate_on_submit()
        else:
            return False;

        
class DomForm(FlaskForm):
    submitField = wtf.SubmitField('submit')
    builtin_label_types=(wtf.SubmitField, wtf.HiddenField)
    def __init__(self, title=False, action_url=""):
        super().__init__()
        self.frame = fieldSet(title if title else self.__doc__)
        self.formTag = tags.form(method="POST", 
                                 action=action_url, 
                                 target="_self", 
                                 name=self.__class__.__name__)
        self.formTail = tags.div()
        self.submitField.id = self.submitField.name = \
                str(self.__class__.__name__) + "SubmitField"
        
    @property
    def content(self):
        with self.frame.add(self.formTag):
            raw(self.hidden_tag())
            for eachField in self:
                if eachField == self.submitField:
                    continue
                if not isinstance(eachField, self.builtin_label_types):
                    raw(eachField.label())
                raw(eachField())
            raw(self.submitField())
        self.frame.add(self.formTail)
        return self.frame

    @property
    def was_submitted(self):
        if self.submitField.name in flask.request.form:
            return self.validate_on_submit()
        else:
            return False;


class LoginForm(DomForm):
    "Provide a login form"
    user = wtf.StringField("User", default="guest", validators=[DataRequired()])
    guessword = wtf.PasswordField("Password", validators=[DataRequired()])

class ImportSeriesForm(DomForm):
    seriesSelect = wtf.SelectField("Choose from existing vimeo folders: ")
    seriesDate = wtf.DateField("First recorded:", default=date.today)
    #passwd = wtf.PasswordField("Password", default='(auto generate)')
    submitField = wtf.SubmitField("Import")

    def __init__(self, catalog):
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
        self.seriesSelect.choices = list(zip(us, usn))



class DeleteSeriesForm(DomForm):
    "Delete series from catalog"
    submitField = wtf.SubmitField('Delete Series...')

class DateSeriesForm(DomForm):
    "Date series from catalog"
    recordedDate = wtf.DateField("Started on", 
                                 [DataRequired()], 
                                 default=date.today)
    vidSelect = wtf.SelectMultipleField("Lessons")
    submitField = wtf.SubmitField('Date Series...')

    def __init__(self, series):
        super().__init__(f"Modify {series.name} start Date")
        # get the names associated with the vimeo folders
        vn = [ x.name for x in series.videos ]
        self.vidSelect.choices = list(zip(vn, vn))

class NormalizeNameSeriesForm(DomForm):
    "Normalize the name of the lessons in the series"
    vidSelect = wtf.SelectMultipleField("Lessons")
    submitField = wtf.SubmitField('Autoname Series...')

    def __init__(self, series):
        super().__init__(f"Modify {series.name} start Date")
        # get the names associated with the vimeo folders
        vn = [ x.name for x in series.videos ]
        self.vidSelect.choices = list(zip(vn, vn))

class AddVideosForm(DomForm):
    "Add video to the series"
    name_fld = wtf.StringField("Video title:", [DataRequired()])
    recd_fld = wtf.DateField("Recorded:", [DataRequired()], default=date.today)
    submitField = wtf.SubmitField("Begin upload...")
    def __init__(self, series):
        super().__init__(f"Add video to {unquote(series.name)}")
        if self.was_submitted:
            self.name_fld.render_kw = {'disabled': 'disabled'}
            self.recd_fld.render_kw = {'disabled': 'disabled'}
            self.submitField.render_kw = {'disabled': 'disabled'}
        else:
            if len(series.videos):
                latest_vid = series.videos[-1]
                self.name_fld.data = latest_vid.next_name
            else:
                self.name_fld.data = "Lesson #1"

    @property
    def video_name(self):
        return flask.request.args.get('vid_name', self.name_fld.data)
        #return flask.session.get('vidName', 

    @property
    def record_date(self):
        return flask.request.args.get('vid_rec_date', self.recd_fld.data)
        #return flask.session.get('recDate', 

    @property
    def uploaded_uri(self):
        return flask.request.args.get('video_uri', False)

    def initiate_upload(self, series):
        upact = series.uplink(self.video_name, 
                              "TODO: Description",  
                              flask.request.url)
        req = PreparedRequest()
        req.prepare_url(upact, 
                        {'video_name':self.video_name,
                         'vid_rec_date':self.record_date})
        self.formTail.add(
            tags.form(
                tags.input(name="file_data", type="file"), 
                tags.input(type="submit"),
                method="POST",
                enctype="multipart/form-data",
                name="upload", 
                action=req.url))
        return "Waiting for file submission..."

    @property 
    def was_uploaded(self):
        return self.uploaded_uri

    def process_upload(self, series):
        return executor.monitor(series.process_upload,
                                self.video_name, 
                                self.record_date, 
                                self.uploaded_uri)

class PurgeVideoForm(DomForm):
    "Purge video from catalog (but NOT from vimeo)"
    submitField = wtf.SubmitField('Purge this Video')

class SeriesForm(DomForm):
    def __init__(self, series):
        self._series = series

class VideoUploaderForm(SeriesForm):
    def __init__(self, series):
        super().__init__(series,
            f"Add video(s) to {series.name}:",
            InputExpander("Video", 
                wtf.FileField("Select a video file:"), 
                maxcnt=2))

    def process(self):
        for video_input in self.fileSelectors:
            series.upload_a_video(**video_input)
        self.status = f"Uploading videos..."

class SyncVideosForm(DomForm):
    def process(self):
        series.sync_with_vimeo()
        self.status = f"Syncronizing {series.name} with vimeo..."

