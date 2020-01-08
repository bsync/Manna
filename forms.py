from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired

class PasswordForm(FlaskForm):
    guessword = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')
