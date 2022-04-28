import flask, os, requests, json
import wtforms.validators as validators
from flask_mail import Message
from tables import UserTable
from models import mdb, User, Role
from wtforms.fields import StringField, PasswordField
from wtforms.fields import IntegerField, HiddenField, FileField
from wtforms.fields import SubmitField, TextAreaField
from wtforms.fields.html5 import DateField, EmailField
from wtforms.fields import FormField, FieldList
from flask_wtf import FlaskForm, RecaptchaField
from flask_login import current_user
from oauthlib.oauth2 import WebApplicationClient
from datetime import date

def redirect(url='', to_form=None, with_msg=False, **kwargs): 
    if to_form is not None:
        if hasattr('id', to_form):
            to_form = to_form.id 
        url = f"{url}#{to_form}"
    if with_msg:
        if not isinstance(with_msg, str):
            with_msg = " ".join(with_msg)
        flask.flash(with_msg, to_form)
    url += "&".join([f"?{k}={v}" for k,v in kwargs.items()])
    return flask.redirect(url)

class MannaForm(FlaskForm):
    template = "forms_base.html"
    target = ""
    scripts = [ "https://code.jquery.com/jquery-3.6.0.min.js"]
    vimeo_token_field = HiddenField(default=os.getenv('VIMEO_TOKEN'))
    submit = SubmitField("Submit")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = self.submit.id = self.__class__.__name__

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def was_submitted(self):
        if self.validate_on_submit():
            return flask.request.form['submit'] == self.submit.label.text

    @property
    def visifields(self):
        return [ x for x in self if not isinstance(x, (HiddenField,)) ]

    def on_validated(self):
        pass

    def __getattr__(self, name):
        if name in flask.request.form:
            return flask.request.form['name']
        else:
            raise AttributeError(f"{name} not found in {self}")


class AddSeriesToCatalogForm(MannaForm):
    series_name = StringField("Name the Series", [validators.InputRequired()])
    submit = SubmitField("Add_a_series_to_the_catalog")

class SyncWithCatalogForm(MannaForm):
    submit = SubmitField("Sync_entire_catalog_with_backing_store")

    def on_validated(self):    
        self.mstore.clear_cache()
        self.redirection=redirect(with_msg=f"Cached series have been refreshed...")


class AddVideoForm(MannaForm):
    video_name = StringField("Video Name:", [validators.InputRequired()])
    video_author = StringField("Presented by:", [validators.InputRequired()])
    video_description = StringField("Description:", default=" ")
    video_file = FileField("Video File:", [validators.InputRequired()])
    video_date = DateField("Video Date:", [validators.InputRequired()], default=date.today())
    vid_id = HiddenField("uploaded video ids")
    series_id = HiddenField("series id")
    series_uri = HiddenField("series uri")

    @property
    def visifields(self):
        return [ x for x in self if not isinstance(x, (HiddenField, SubmitField)) ]


class AddVideoSet(MannaForm):
    upload = FieldList(FormField(AddVideoForm), min_entries=2, max_entries=2)
    submit = SubmitField("Upload_Videos", id="upload_videos")
    vimeo_token = os.getenv('VIMEO_TOKEN')
    scripts = ["https://code.jquery.com/jquery-3.6.0.min.js", "vimeo-upload.js", ]

    def __init__(self, series, *args, **kwargs):
        super().__init__(*args, **kwargs)
	#Initialize the data for each series
        nvn = series.next_vidnames(2)
        for avf,vn in zip(self.upload, nvn):
           avf.video_name.data = vn
           avf.video_author.data = series.author
           avf.series_id.data = series.id

    def on_validated(self):    
        vidids = [ vid for vid in flask.request.form.getlist('vid_id') if vid ]
        if len(vidids):
            self.vidnames = flask.request.form.getlist('video_name')[:len(vidids)]
            flask.flash(f"Added {self.vidnames} to {self.series.name}") 
        else:
            flask.flash(f"Must provide at least one video to add to {self.series.name}.")


class AddToRecentVideosForm(MannaForm):
    pass


class PurgeVideo(MannaForm):
    video_to_purge = HiddenField()
    submit = SubmitField("Purge_Video")

    def __init__(self, series, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.series = series

    def on_validated(self):    
        resp = self.series.purge_video(self.video_to_purge.data)
        if resp.status_code != 204:
            self.redirection = redirect(to_form="purge_tab", with_msg=resp.text)
        else:
            self.redirection = redirect(to_form="purge_tab", with_msg=f"Purged {self.video_to_purge.data}")


class RedateSeries(MannaForm):
    start_date = DateField(id="start_date") 
    date_inc = IntegerField(id="date_inc", default=3, render_kw=dict(size=2))
    vid_set = IntegerField(id="vid_set", default=2, render_kw=dict(size=2))
    submit = SubmitField("Redate_Videos", id="redate_videos")

    def __init__(self, series, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_date(value=date.today().isoformat())
        self.series = series


class NormalizeTitles(MannaForm):
    submit = SubmitField("Normalize_Titles")

    def __init__(self, series, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.series = series
        if not self.is_normalizable:
            self.booleans = "disabled" 
        self.prefix = f"""
            <p> {self.example} </p>
            <div id='Normalize_form_results' style="background-color:black; color:red;"></div> """

    @property
    def videos(self):
        return self.series.normalizable_vids

    @property
    def is_normalizable(self):
        return len(self.series.normalizable_vids) > 0

    @property
    def example(self):
        if self.is_normalizable:
            evids = self.series.normalizable_vids
            evid = evids[0]
            e_norm_name = self.series.normalized_name(evid.name)
            return f"""There are a total of {len(evids)} videos to normalize. 
                       For example: {evid.name} would be normalized to {e_norm_name}"""
        else:
            return f"""Nothing to normalize in series "{self.series.name}" at this time.""" 


class SyncSeries(MannaForm):
    template = "sync_form.html"
    submit = SubmitField("Sync_Videos")

    def on_validated(self):    
        flask.flash(f"Resynced series {self.series.name}.")


class RegistrationForm(MannaForm):
    template = "regform.html"
    rendopts=dict(disabled=True)
    submit = None
    register = SubmitField("Register", render_kw=rendopts)
    unregister = SubmitField("Unregister", render_kw=rendopts)
    delete = SubmitField("Delete", render_kw=rendopts)
    promote = SubmitField("Promote", render_kw=rendopts)
    demote = SubmitField("Demote", render_kw=rendopts)
    user_selection = HiddenField()

    def __init__(self, login_manager):
        super().__init__()
        self.table = UserTable(login_manager.Users, select={ 'style':'single'}) 
        self.scripts.extend(self.table.scripts)
        self.css = self.table.css

    @property
    def scriptage(self):
        return f"var dtable = {self.table.scriptage}\n" + \
                """dtable.on('select', (e,dt,type,idxs) => { 
                    var udata = dt.data()
                    var uregd = udata[2] == "True"
                    var uid = udata[3]
                    var isadmin = udata[0] == "Admin"
                    $('#user_selection').val(uid); 
                    $('#register').prop('disabled', uregd)
                    $('#unregister').prop('disabled', !uregd || uid == "1")
                    $('#promote').prop('disabled', isadmin || uid == "1")
                    $('#demote').prop('disabled', !isadmin || uid == "1")
                    $('#delete').prop('disabled', uregd)
                })"""

    @property
    def selected_user(self):
        sid = flask.request.form.get('user_selection', '')
        return User.query.filter_by(id=sid).first() if sid else None

    @property
    def operation(self):
        for op in "register unregister promote demote delete".split():
            if op in flask.request.form:
                return flask.request.form[op]
        return None

    def on_validated(self):    
        su = self.selected_user
        aRole = Role.query.filter(Role.name == 'Admin').first()
        if su:
            if self.operation in "Register Unregister".split():
                su.active = (self.operation == "Register")
            elif self.operation == "Promote":
                if aRole not in su.roles:
                    su.roles.append(aRole)
            elif self.operation == "Demote":
                if aRole in su.roles:
                    su.roles.clear()
            elif self.operation == "Delete":
                mdb.session.delete(su)
            mdb.session.commit()
        self.redirection=redirect(with_msg=f"{self.operation} completed!")


class InviteUserForm(MannaForm):
    #template = "invform.html"
    email = EmailField('Email address', [validators.DataRequired(), validators.Email()])
    submit = SubmitField("Invite")

    def __init__(self, login_manager):
        super().__init__()
        self.lm = login_manager

    def on_validated(self):
        email = self.email.data
        user, user_email = self.lm.db_manager.get_user_and_user_email_by_email(email)
        if user:
            flash("User with that email has already registered", "error")
            return redirect(flask.url_for('user.invite_user'))

        # Add UserInvitation
        user_invitation = self.lm.db_manager.add_user_invitation(
            email=email,
            invited_by_user_id=current_user.id)
        self.lm.db_manager.commit()

        try:
            # Send invite_user email
            self.lm.email_manager.send_invite_user_email(current_user, user_invitation)
        except Exception as e:
            # delete new UserInvitation object if send fails
            self.lm.db_manager.delete_object(user_invitation)
            self.lm.db_manager.commit()
            raise

        # Flash a system message
        flask.flash('Invitation has been sent.', 'success')

        # Redirect
        safe_next_url = self.lm._get_safe_next_url('next', 'list_latest')
        self.redirection = redirect(safe_next_url)

class RequestAccessForm(MannaForm):
    template = "request_access_form.html"
    email = EmailField('Email address', [validators.DataRequired(), validators.Email()])
    comments = TextAreaField(
        u'Your comments:', 
        [validators.optional(), validators.length(max=200)])
    recaptcha = RecaptchaField()
    submit = SubmitField("Request_Access")

    def on_validated(self):    
        mailer = self.lm.email_adapter.mail
        rcpt = self.lm.USER_EMAIL_SENDER_EMAIL
        msg = Message("Request for Manna Access", recipients=[rcpt])
        msg.body = f"{self.email.data} says '{self.comments.data}'"
        mailer.send(msg)
        self.redirection=redirect(with_msg="Request sent....please allow a day or so for response")


class GoogleLoginForm(MannaForm):
    template = "google_login_form.html"
    submit = SubmitField("Google_Authorize")

class LoginUserForm(MannaForm):
    template = "login_form.html"
    email = EmailField('Email address', [validators.DataRequired(), validators.Email()])
    password = PasswordField("Password", [validators.DataRequired()])
    recaptcha = RecaptchaField()
    submit = SubmitField("Login")

    def __init__(self, login_manager):
        super().__init__()
        if not self.email.data and login_manager.guest:
            self.email.data  = login_manager.guest.email
        
