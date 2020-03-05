import os
import dominate.tags as tags
import flask
import wtforms as wtf
import vimongo
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
    builtin_label_types=(wtf.SubmitField, wtf.HiddenField)
    response = None
    def __init__(self, title=False):
        super().__init__()
        self.frame = groupedTags(title if title else self.__doc__)
        self.formTag = tags.form(method="POST", action="", target="_self")
        self.formTail = tags.div()

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
    def action(self):
        return self.formTag['action']

    @action.setter
    def action(self,value):
        self.formTag['action']=value

    @property
    def target(self):
        return self.formTag['target']

    @target.setter
    def target(self,value):
        self.formTag['target']=value

    def valid_submission_with(self, submitField):
        if submitField.id in flask.request.form:
            return self.validate_on_submit()
        else:
            return False;

class PasswordForm(DomForm):
    "Provide a password"
    guessword = wtf.PasswordField("Password", validators=[DataRequired()])
    submitField = wtf.SubmitField('submit')

    def __init__(self, target):
        super().__init__(f"Provide a password for {target}")
        import passcheck
        if self.valid_submission_with(self.submitField):
            self.passes = passcheck(target, self.data['guessword'])
            if not self.passes:
                flask.flash(f"Wrong password for {target}")
        else:
            self.passes = False


class AddSeriesForm(DomForm):
    "Add a new series to the catalog"
    seriesName = wtf.StringField("Series Name", [DataRequired()]) 
    seriesDesc = wtf.TextAreaField("Series Description", [DataRequired()])
    addSeriesField = wtf.SubmitField('Add')

    def __init__(self, seriesCatalog):
        super().__init__()
        if self.valid_submission_with(self.addSeriesField):
            name = self.seriesName.data
            description = self.seriesDesc.data
            try:
                seriesCatalog.addAlbum(name, description)
                flask.flash(f"Added album {name}")
            except Exception as e:
                flask.flash(f"Failed to create album: {str(e)}")


class DeleteSeriesForm(DomForm):
    "Delete video from series"
    deleteField = wtf.SubmitField('Delete Empty Series...')
    qscriptage = """$('#{deleteFieldId}').prop("disabled", {disabled})
                    $('#{deleteFieldId}').click( 
                        function () {{ 
                            return confirm("Delete series: {alb_name} ?") 
                        }} ) """

    def __init__(self, series):
        super().__init__()
        self.qscriptage = self.qscriptage.format(
                                deleteFieldId=self.deleteField.id,
                                disabled=str(len(series.videos) > 0).lower(),
                                alb_name=series.name)
        if self.valid_submission_with(self.deleteField):
            try:
               if len(series.videos): 
                    flask.flash(f"Album {series.name} not empty!")
               else:
                    series.delete()
                    flask.flash(f"Deleted {series.name}")
            except Exception as e:
                flask.flash(f"Failed deleting {series.name}: {e}")

def wtf_require(ftype, title, **kwargs):
    return ftype(title, [DataRequired()], **kwargs)

class AddVideosForm(DomForm):
    "Add video to the series"
    videoNameField = wtf_require(wtf.StringField, "Video title:")
    videoDescField = wtf_require(wtf.TextAreaField,"Video description:")
    recordedDate = wtf_require(DateField,"Recorded on", default=date.today)
    submitUpload = wtf.SubmitField("Begin upload...")

    def __init__(self, alb):
        super().__init__()
        if self.valid_submission_with(self.submitUpload):
            del self.submitUpload
            vub=dict(
                 upload=dict(approach="post", redirect_url=flask.request.url),
                 name=self.videoNameField.data,
                 description=self.videoDescField.data)
            vu = vimongo.vcpost("/me/videos", **vub).json()
            self.formTail.add(raw(vu['upload']['form']))
        else:
            import pdb; pdb.set_trace()
            preName = alb.videos[-1].name
            self.videoNameField.data = preName
            self.videoDescField.data = "preset goes here"

        viduri=flask.request.args.get('video_uri', False)
        if viduri:
            vp = vimongo.vcput(f"{alb.id}{viduri}")
            alb.synchronize()
            flask.flash(f"Video {viduri} added to vimeo")
            self.response=f"/manna/{viduri}"


class SyncToVimeoForm(DomForm):
    "Syncronize album or entire catalog with vimeo content"
    syncField = wtf.SubmitField('Syncronize')

    def __init__(self, catalb):
        if isinstance(catalb, vimongo.AlbumRecord):
            super().__init__("Syncronize the series with vimeo")
        else:
            super().__init__("Syncronize the catalog with vimeo")
        if self.valid_submission_with(self.syncField):
            catalb.synchronize()
            flask.flash(f"Series {catalb.name} now synchronized with vimeo")


class PurgeVideoForm(DomForm):
    "Purge video from catalog (but NOT from vimeo)"
    purgeField = wtf.SubmitField('Purge this Video')
    qscriptage = """$('#{purgeFieldId}').click( 
                        function () {{ 
                            return confirm("Purge video: {vid_name} ?") 
                        }} )"""

    def __init__(self, vid):
        super().__init__()
        self.qscriptage = self.qscriptage.format(
                                purgeFieldId=self.purgeField.id,
                                vid_name=vid.name)
        if self.valid_submission_with(self.purgeField):
            vid.delete()
            flask.flash(f"Video {vid.name} purged from catalog")
            flask.redirect("/")

