import wtforms
import dominate.tags as tags
from dominate.util import raw
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired

class DomForm(FlaskForm):
    submitField = wtforms.SubmitField('Submit')

    def __init__(self, title=None):
        super().__init__()
        if title is None: 
            self.title = self.__class__.__name__
        else:
            self.title = title

    @property
    def as_dom_tag(self):
        tf = tags.form(method="POST")
        with tf:
            tags.div(self.title)
            for key in self.data:
                ff = getattr(self, key)
                if type(ff) == wtforms.StringField:
                    raw(f"{ff.label} : {ff()}")
                else:
                    raw(str(ff))
        return tf
    

class PasswordForm(DomForm):
    guessword = wtforms.PasswordField("Password", validators=[DataRequired()])

class CatalogEditor(DomForm):
    seriesField = wtforms.StringField("Series", validators=[DataRequired()])
    descriptField = wtforms.StringField("Description", 
                                        validators=[DataRequired()])
    submitField = wtforms.SubmitField('Add')

    @property
    def series(self):
        return self.seriesField.data

    @property
    def description(self):
        return self.descriptField.data

