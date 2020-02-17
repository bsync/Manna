import os
import dominate.tags as tags
import flask, flask_wtf
from dominate.util import raw
from urllib.parse import unquote
from wtforms import StringField, TextAreaField, PasswordField, FileField, SubmitField
from wtforms.validators import DataRequired
from vimongo import sync_mongo_and_vimeo


class DomForm(flask_wtf.FlaskForm):
    def __init__(self, title=None):
        super().__init__()
        title=title if title else self.__class__.__name__
        self.content = tags.form(method="POST")
        self.sDiv = tags.div("", id="status", style="color: red;")
        self.content.add(raw(str(self.hidden_tag())), self.sDiv)

    def formFieldSet(self, fs_name, *fields):
        with self.content:
            with tags.fieldset(tags.legend(fs_name)):
                with tags.div():
                    for field in fields:
                        if field.type == "SubmitField":
                            tags.br()
                            raw(str(field))
                        else:
                            raw(str(field.label))
                            raw(field())

    @property
    def status(self):
        return self.sDiv[0]
        
    @status.setter
    def status(self, value):
        self.sDiv[0] = value
    

class PasswordForm(DomForm):
    guessword = PasswordField("Password", validators=[DataRequired()])
    submitField = SubmitField('submit')

    def __init__(self, target):
        resource=unquote(os.path.split(target)[-1])
        super().__init__(f"Provide password for: {resource}")
        self.formFieldSet("Submit password:", self.guessword, self.submitField)


class EditCatalogForm(DomForm):
    seriesField = StringField("Series", render_kw=dict(style="width:100%;"))
    descriptField = TextAreaField("Description", 
                                  render_kw=dict(style="width:100%;", rows="5")) 
    addSeriesField = SubmitField('Add')
    vimeoSyncField = SubmitField("VimeoSync")
    qscriptage = """function vSync() {
        $.ajax({ url: '/manna/vsync', 
                 success: function(data) { $('#sync').html(data); },
                 complete: function() { 
                    if( $('#sync').text() != 'Done' ) { 
                        setTimeout(vSync, 5000); } } }); } """

    def __init__(self, seriesCatalog):
        super().__init__(f"Edit Catalog:")
        self.formFieldSet("Add a new series to the catalog",
                          self.seriesField, 
                          self.descriptField,
                          self.addSeriesField)
        self.formFieldSet("Synchronize catalog with Vimeo", self.vimeoSyncField)

        if self.validate_on_submit():

            if self.vimeoSyncField.data:
                self.status = "TODO: vimeo sync entire catalog"

            if self.addSeriesField.data:
                name = self.seriesField.data
                description = self.descriptField.data
                try:
                    if len(name) == 0 or len(description) == 0: 
                        raise Exception("Please provide a name and description")
                    seriesCatalog.addAlbum(name, description)
                    self.status = f"Added album {name}"
                except Exception as e:
                    self.status = f"Failed to create album: {str(e)}"


class SeriesForm(DomForm):
    deleteField = SubmitField('Delete Empty Series', id="delete_button")
    addVideoField = FileField('Add new video...', id="add_button")
    syncVimeoField = SubmitField('VimeoSync')
    qscriptage = """$(document).ready(function() {
        $("#delete_button").click(function () { 
           return window.confirm("Confirm Delete?") } )
        $("#add_button").on("change", function(e) {
            // Get the selected file from the input element
            var file = e.target.files[0]
            // Create a new tus upload
            var upload = new tus.Upload(file, {
                endpoint: "http://localhost:1080/files/",
                retryDelays: [0, 3000, 5000, 10000, 20000],
                metadata: { filename: file.name, filetype: file.type },
                onError: function(error) {
                    console.log("Failed because: " + error)
                },
                onProgress: function(bytesUploaded, bytesTotal) {
                    var percentage = (bytesUploaded 
                                     / bytesTotal * 100).toFixed(2)
                    console.log(bytesUploaded, 
                                bytesTotal, 
                                percentage + "%")
                },
                onSuccess: function() {
                    console.log("Download %s from %s", 
                                upload.file.name, 
                                upload.url)
                } })
                upload.start() })})"""

    def __init__(self, alb):
        super().__init__("Edit the Series")
        if len(alb.videos) == 0: 
            self.formFieldSet("Delete empty series", self.deleteField)
        self.formFieldSet("Add new videos to the series", self.addVideoField)
        self.formFieldSet("Syncronize series with vimeo content", self.syncVimeoField)
        if self.validate_on_submit():
            if self.deleteField.data:
                try:
                    if len(alb.videos): 
                        raise Exception(f"Album {alb.name} not empty!")
                    alb.delete()
                    self.status = f"Deleted {alb.name}"
                except Exception as e:
                    self.status = f"Failed deleting {alb.name}: {e}"
                       
            if self.addVideoField.data:
                self.status = "TODO: Support uploading a new video."


