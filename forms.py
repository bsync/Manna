import flask
import dominate.tags as tags
import wtforms as wtf
import executor
from flask_wtf import FlaskForm
from dominate.util import raw
from urllib.parse import unquote
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DateField
from requests.models import PreparedRequest
from datetime import date

@tags.fieldset
def groupedTags(fs_name, *fs_tags):
    if fs_name is None: 
        container = tags.div()
    else:
        container = tags.legend(fs_name)
    with container:
        for fs_tag in fs_tags:
            fs_tag()
        
class DomForm(FlaskForm):
    submitField = wtf.SubmitField('submit')
    builtin_label_types=(wtf.SubmitField, wtf.HiddenField)
    def __init__(self, title=False):
        super().__init__()
        self.frame = groupedTags(title if title else self.__doc__)
        self.formTag = tags.form(method="POST", action="", 
                                 target="_self", name=self.__class__.__name__)
        self.formTail = tags.div()
        self.submitField.id = self.submitField.name = \
                str(self.__class__.__name__) + "SubmitField"
        
    @property
    def content(self):
        with self.frame.add(self.formTag):
            raw(self.hidden_tag())
            for eachField in self:
                if not isinstance(eachField, self.builtin_label_types):
                    raw(eachField.label())
                raw(eachField())
        self.frame.add(self.formTail)
        return self.frame

    @property
    def was_submitted(self):
        if self.submitField.name in flask.request.form:
            return self.validate_on_submit()
        else:
            return False;


class PasswordForm(DomForm):
    "Provide a password"
    user = wtf.StringField("User", default="guest", validators=[DataRequired()])
    guessword = wtf.PasswordField("Password", validators=[DataRequired()])

    def __init__(self, target):
        super().__init__(f"Provide a password for {unquote(target)}")
        self.target = target
        try:
            import passcheck
            if self.was_submitted:
                self.passes = passcheck(target, self.data)
                if not self.passes:
                    flask.flash(f"Wrong password for {unquote(target)}")
            else:
                self.passes = False
        except:
            self.passes = True


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


class AddSeriesForm(DomForm):
    "Add a new series to the catalog"
    seriesName = wtf.StringField("Series Name", [DataRequired()]) 
    seriesDesc = wtf.TextAreaField("Series Description", [DataRequired()])
    submitField = wtf.SubmitField('Add')

    @property
    def name(self):
        return self.seriesName.data

    @property
    def description(self):
        return self.seriesDesc.data


class DeleteSeriesForm(DomForm):
    "Delete series from catalog"
    submitField = wtf.SubmitField('Delete Series...')

class DateSeriesForm(DomForm):
    "Date series from catalog"
    recordedDate = wtf.DateField("Started on", 
                                 [DataRequired()], 
                                 default=date.today)
    fromSelect = wtf.SelectField("From: ")
    toSelect = wtf.SelectField("To: ")
    submitField = wtf.SubmitField('Date Series...')

    def __init__(self, series):
        super().__init__(f"Modify {series.name} start Date")
        # get the names associated with the vimeo folders
        vn = [ x.name for x in series.videos ]
        self.fromSelect.choices = list(zip(vn, vn))
        vn.reverse()
        self.toSelect.choices = list(zip(vn, vn))

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

class SyncWithVimeoForm(DomForm):
    "Syncronize album or entire catalog with vimeo content"
    submitField = wtf.SubmitField('Syncronize')

class ResetToVimeoForm(DomForm):
    "Syncronize album or entire catalog with vimeo content"
    submitField = wtf.SubmitField('Reset')

class PurgeVideoForm(DomForm):
    "Purge video from catalog (but NOT from vimeo)"
    submitField = wtf.SubmitField('Purge this Video')
