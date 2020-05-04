import os
import dominate.tags as tags
import flask
import wtforms as wtf
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from dominate.util import raw
from urllib.parse import unquote
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DateField
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


class AddSeriesForm(DomForm):
    "Add a new series to the catalog"
    seriesName = wtf.StringField("Series Name", [DataRequired()]) 
    seriesDesc = wtf.TextAreaField("Series Description", [DataRequired()])
    submitField = wtf.SubmitField('Add')


class DeleteSeriesForm(DomForm):
    "Delete series from catalog"
    submitField = wtf.SubmitField('Delete Series...')

class DateSeriesForm(DomForm):
    "Date series from catalog"
    recordedDate = wtf.DateField("Started on", 
                                 [DataRequired()], 
                                 default=date.today)
    submitField = wtf.SubmitField('Date Series...')

class AddVideosForm(DomForm):
    "Add video to the series"
    vidName = wtf.StringField("Video title:", [DataRequired()])
    vidDesc = wtf.TextAreaField("Video description:")
    recordedDate = wtf.DateField("Recorded on", 
                                 [DataRequired()], 
                                 default=date.today)
    submitField = wtf.SubmitField("Begin upload...")

    def __init__(self, alb):
        super().__init__(f"Add video to {unquote(alb.name)}")
        if not self.was_submitted: #Initialize main form configuration
            if len(alb.videos):
                latest_vid = alb.videos[-1]
                self.vidName.data = latest_vid.next_name
                self.vidDesc.data = latest_vid.description
            else:
                self.vidName.data = "Lesson #1"
        else:
            self.integrate_upload_form( 
                alb.upload_action(
                    self.vidName.data, 
                    self.vidDesc.data, 
                    flask.request.url
                    )
                )

    def integrate_upload_form(self, upurl):
        self.submitField.render_kw = {'disabled': 'disabled'}
        self.formTail.add(
            tags.form(
                tags.input(name="file_data", type="file"), 
                tags.input(type="submit"),
                method="POST",
                enctype="multipart/form-data",
                name="upload", 
                action=upurl))

class SyncWithVimeoForm(DomForm):
    "Syncronize album or entire catalog with vimeo content"
    submitField = wtf.SubmitField('Syncronize')

class ResetToVimeoForm(DomForm):
    "Syncronize album or entire catalog with vimeo content"
    submitField = wtf.SubmitField('Reset')

class PurgeVideoForm(DomForm):
    "Purge video from catalog (but NOT from vimeo)"
    submitField = wtf.SubmitField('Purge this Video')
