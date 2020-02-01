import wtforms
import dominate.tags as tags
from dominate.util import raw
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired

class DomForm(FlaskForm):
    submit = wtforms.SubmitField('Submit')

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
    series = wtforms.StringField("Series", validators=[DataRequired()])
    submit = wtforms.SubmitField('Add')
