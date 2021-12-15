import flask, os, requests, json
import wtforms.validators as validators
from flask_mail import Message
from tables import VideoTable, UserTable
from vidstore import MannaStore
from models import mdb, User, Role
from wtforms.fields import StringField, PasswordField
from wtforms.fields import IntegerField, HiddenField, FileField
from wtforms.fields import SelectField, SubmitField, TextAreaField
from wtforms.fields.html5 import DateField, EmailField
from flask_wtf import FlaskForm, RecaptchaField
from flask_login import current_user
from oauthlib.oauth2 import WebApplicationClient
from datetime import date

def redirect(url='', to_form=None, with_msg=False, **kwargs): 
    if to_form is not None:
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
        self.mstore = MannaStore()
        self.today=f"{date.today().isoformat()}"
        self.template_vars = dict(form=self)

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def was_submitted(self):
        return self.validate_on_submit() and flask.request.form['form_id'] == self.name

    @property
    def content_fields(self):
        yfields = [ RecaptchaField, StringField, EmailField, 
                    PasswordField, TextAreaField, SelectField ]
        for field in self._fields.values():
            if type(field) in yfields:
                yield field

    @property
    def submit_fields(self):
        for field in self._fields.values():
            if type(field) in [ SubmitField ]:
                yield field

    def on_validated(self):
        pass

    def __getattr__(self, name):
        if name in flask.request.form:
            return flask.request.form['name']
        else:
            raise AttributeError(f"{name} not found in {self}")


class AddSeriesToCatalogForm(MannaForm):
    submit = SubmitField("Add_a_series_to_the_catalog")
    series_name = StringField("Name the Series", [validators.InputRequired()])

    def on_validated(self):    
        aseries = self.mstore.add_new_series(self.series_name.data, "TODO: Describe me")
        self.redirection=redirect(with_msg=f"Added series {aseries.name}")


class SyncWithCatalogForm(MannaForm):
    submit = SubmitField("Sync_entire_catalog_with_backing_store")

    def on_validated(self):    
        self.mstore.clear_cache()
        self.redirection=redirect(with_msg=f"Cached series have been refreshed...")


class SeriesForm(MannaForm):
    submit = SubmitField("Series_Form")
    table_options = { 'pageLength':5 }

    def __init__(self, series, *args, **kwargs):
        self.series = series
        super().__init__(*args, **kwargs)
        tbopts = dict(pageLength=5)
        tbopts.update(self.table_options)
        self.table = VideoTable(self.videos, **tbopts)
        self.template_vars.update(self.table.template_vars)
        self.scripts.extend(self.table.scripts)
        self.css = self.table.css
    
    @property
    def scriptage(self):
        return self.table.scriptage

    @property
    def videos(self):
        return self.series.videos()


class AddVideoForm(SeriesForm):
    submit = SubmitField("Add_Video")
    video_name = StringField("Video Name:")
    #video_name = StringField("Video Name:", [validators.InputRequired()])
    video_author = StringField("Presented by:")
    #video_author = StringField("Presented by:", [validators.InputRequired()])
    video_file = FileField("Video File:")
    #video_file = FileField("Video File:", [validators.InputRequired()])
    video_date = DateField("Video Date:", default=date.today())
    #video_date = DateField("Video Date:", [validators.InputRequired()], default=date.today())
    series_id = HiddenField("series id")
    series_uri = HiddenField("series uri")
    vid_id = HiddenField("uploaded video ids")


class AddVideoSetForm(SeriesForm):
    template = "add_video_set.html"
    submit = SubmitField("Upload_Videos", id="upload_videos")

    def __init__(self, series, cnt=2, *args, **kwargs):
        super().__init__(series, *args, **kwargs)
        self.legend = f"Upload videos to {series.name}"
        self.vimeo_token = os.getenv('VIMEO_TOKEN')
        self.vidups = []
        for vidx in range(0,cnt):
            self.vidups.append(
                AddVideoForm(series, 
                             *args, 
                             video_name=series.nth_next_vidname(vidx+1)))
        self.scripts.extend([ 
            "https://code.jquery.com/jquery-3.6.0.min.js", 
            "vimeo-upload.js", ]) 

    def on_validated(self):    
        self.vidids = [ vid for vid in flask.request.form.getlist('vid_id') if vid ]
        import pdb; pdb.set_trace()
        if len(self.vidids):
            self.vidnames = flask.request.form.getlist('video_name')[:len(self.vidids)]
            flask.flash(f"Added {self.vidnames} to {self.series.name}") 
            self.mstore.purge_cache(self.series)
        else:
            flask.flash(f"Must provide at least one video to add to {self.series.name}.")

    @property
    def scriptage(self):
        return """
            $(".upunit:not(:first)").hide()
            $(".del_field").hide()
            $(".add_field").click(function(e) {
                e.preventDefault()
                if ($(".upunit:hidden").length > 0) {
                        $(".upunit:hidden:first").show()
                } 
                if ($(".upunit:hidden").length == 0) {
                        $(".add_field").hide()
                        $(".del_field").show()
                }
            })
            $(".del_field").click(function(e) {
                e.preventDefault()
                if ($(".upunit:visible").length > 0) {
                        $(".upunit").last().hide()
                } 
                if ($(".upunit:visible").length == 1) {
                        $(".add_field").show()
                        $(".del_field").hide()
                }
            }) 

            $("#upload_videos").click(function(evt) {
               evt.stopPropagation()
               evt.preventDefault()
               var ups = $.map($(".upunit:visible"), function(unit) { return perform_upload_for(unit) })
               $.when(ups).done(function() { $("#AddVideoSetForm").submit() })
            })

            function perform_upload_for(unit) {
               var upfile = $(unit).children(".video_file")[0].files[0]
               var vidname = $(unit).children(".video_name").val()
               var progbar = $(unit).children(".progress")[0]
               var results = $(unit).children(".status")
               var vidout = $(unit).children(".vid_id")
               var vimtoken = $("#vimeo_token_field").val()
               var seriesid = $(unit).children(".series_id").val()
               results.html("")

               function showMessage(html, type) {
                   results.attr('class', 'status alert alert-' + (type || 'success'))
                   results.html(html)
               }

               function move_to_series(vidid) { 
                    return new Promise( (resolve) => {
                        $.ajax({url: `https://api.vimeo.com/me/projects/${seriesid}/videos/${vidid}`,
                                type: "PUT",
                                beforeSend: function(xhr) { 
                                    xhr.setRequestHeader('Authorization', 'Bearer ' + vimtoken); }, 
                                success: function (resp) {
                                    showMessage(`Uploaded <strong>${vidname}</strong> ` +
                                                                    `to series ${seriesid}`)
                                    vidout.val(vidid) 
                                    resolve(vidid)
                                }, 
                                error: function (xhr, ts, ex) {
                                    showMessage(`Upload of <strong>${vidname}</strong> ` +
                                                `to series ${seriesid} failed with error: ${ts}`)
                                }, })
                    })
                }

                function wait_for_transcode(vidid) {
                    var tm=0, timer=setInterval(function(){tm++},1000);
                    showMessage(`Waiting for transcode to complete for: <strong>${vidname}</strong>`)
                    return new Promise( (resolve) => {
                        function poll_transcode_status() {
                            $.ajax({url: `https://api.vimeo.com/videos/${vidid}` 
                                         + "?fields=uri,upload.status,transcode.status",
                                    type: "GET",
                                    beforeSend: function(xhr) { 
                                        xhr.setRequestHeader('Authorization', 
                                                             'Bearer ' + vimtoken); }, 
                                    success: function (resp) {
                                        if (resp.transcode.status != "complete") {
                                            showMessage(`Transcode status after ${tm} seconds: ${vidname} ` 
                                                       +`<strong> ${resp.transcode.status} </strong>` )
                                            setTimeout(poll_transcode_status, 3000, vidid) 
                                        }
                                        else { 
                                            showMessage(`Transcode complete for: <strong> ${vidname} </strong>`)
                                            resolve(vidid)
                                        } } })
                        }
                        poll_transcode_status()
                    })
                }

               vup_promise = new Promise((resolve,reject) => {
                    vup = new VimeoUpload({
                         name: vidname,
                         description: "TODO",
                         private: false,
                         file: upfile,
                         token: vimtoken,
                         upgrade_to_1080: true,
                         onError: function(data) {
                            showMessage('<strong>Error</strong>: ' 
                                        + JSON.parse(data).error, 'danger') },
                         onProgress: function(data) {
                            updateProgress(data.loaded / data.total, progbar) },
                         onComplete: (vuri) => resolve(vuri),
                            })
                    vup.upload() })
                    return vup_promise.then(move_to_series).then(wait_for_transcode)
            }

            function updateProgress(progress, bar) {
                progress = Math.floor(progress * 100)
                $(bar).attr('style', 'background-color: blue; width:' + progress + '%')
                $(bar).html('&nbsp;' + progress + '%')
            }
            """


class PurgeVideoFromSeries(SeriesForm):
    submit = SubmitField("Purge_Video")
    vidlist = SelectField("Choose a video to purge:", validate_choice=False) 
    table_options = { 'select':{ 'style':'single'} }

    def __init__(self, series, *args, **kwargs):
        super().__init__(series, *args, **kwargs)
        self.legend = f"Purge videos from {series.name}"
        self.vidlist.choices = [ v.name for v in series.videos() ]

    def on_validated(self):    
        resp = self.series.purge_video(self.vidlist.data)
        if resp.status_code != 204:
            flask.flash(resp.text)
        else:
            flask.flash(f"Purged {self.vidlist.data}")

    @property
    def scriptage(self):
        return """$("#Purge_Video_submit").click(function(evt) {
                    return window.confirm(`Remove ${$('#vidlist').val()}?`)
                }) """


class RedateSeriesForm(SeriesForm):
    template = "redate_form.html"
    submit = SubmitField("Redate_Videos")
    submit = SubmitField("Redate_Videos", id="redate_videos")
    table_options = { 'select':{ 'style':'multi'} }
    start_date = DateField(id="start_date") 
    date_inc = IntegerField(id="date_inc", default=3, render_kw=dict(size=2))
    vid_set = IntegerField(id="vid_set", default=2, render_kw=dict(size=2))

    def __init__(self, series, *args, **kwargs):
        super().__init__(series, *args, **kwargs)
        self.legend = f"Redate videos in {series.name}"
        self.scripts.extend([ "date.format.js" ])

    @property
    def initial_date(self):
        return self.start_date(value=date.today().isoformat())

    @property
    def scriptage(self):
        return f"var dtable = {self.table.scriptage}\n" + \
                """ 
                var selected = [];
                $('#start_date').datepicker({dateFormat: "yy-mm-dd"})
                $('#vid_set').spinner({step: 1, min: 1, max: 3})
                $('#date_inc').spinner({step: 1, min: 1, max: 3})
                function set_redate_strategy(etype) {
                   if (etype === 'row') {
                        var srows = dtable.rows('.selected').data()
                        srows = srows.map(function(v) { return $(v[2]).text() })
                        if ( srows.length == 0) {
                            $('#strategy').text('Redate all items in the order listed ')
                        }
                        else if ( srows.length == 1 ) {
                            $('#strategy').text(`Redate items in the order listed from ${srows[0]} `)
                        }
                        else if ( srows.length == 2 ) {
                            $('#strategy').text(`Redate items in the order listed from ${srows[0]} up to ${srows[1]} `)
                        }
                        else { 
                            $('#strategy').text('Redate the selected items in the order listed')
                        }
                   }
                }
                set_redate_strategy('row')
                function changing_selection(e,dt,type,idxs) { set_redate_strategy(type) }
                dtable.on('select', changing_selection)
                dtable.on('deselect', changing_selection)
                $("#redate_videos").click(
                  function(evt) { 
                    evt.preventDefault()
                    var vc = dtable.rows('.selected').data()
                    if (vc.length == 0) { dtable.rows().select() }
                    else if (vc.length == 2) { 
                        ridxs = dtable.rows().indexes()
                        sidxs = dtable.rows('.selected')
                        sidxs = sidxs.indexes()
                        dtable.rows(
                            /* note: the row indices used by datatables are NOT the same 
                               as the order of the actual table's rows. Therefore we
                               must use indexOf to compare positions.*/
                            function (idx, data, node) { 
                                return ridxs.indexOf(idx) >= ridxs.indexOf(sidxs[0]) && 
                                       ridxs.indexOf(idx) <= ridxs.indexOf(sidxs[1])
                            }).select()
                    }
                    vc = dtable.rows('.selected').data()
                    var vm = vc.map(function(v) { return $(v[2]).text() })
                    var date = new Date($('#start_date').val() + "T00:00")
                    var dinc = parseInt($('#date_inc').val())
                    var vcnt = parseInt($('#vid_set').val())
                    for (let lname of vm.toArray()) {
                        dout = date.format('yyyy-mm-dd')
                        $.ajax({url: escape(`videos/${lname}/edit`)+`?redate=${dout}`, 
                                 async: false,
                                 success: function(result) { 
                                   $('#RedateVideos_form_results').html(result) } })
                        vcnt = vcnt - 1
                        if (vcnt == 0) {
                            vcnt = $('#vid_set').val()
                            date.setDate(date.getDate() + dinc)
                        }
                    }
                    window.location.reload()
                }) 

                """
    

class NormalizeSeries(SeriesForm):
    template = "normalize_form.html"
    submit = SubmitField("Normalize_Titles")

    def __init__(self, series, *args, **kwargs):
        super().__init__(series, *args, **kwargs)
        self.legend = f"Normalize videos in {series.name}"
        if not self.is_noramlizable:
            self.booleans = "disabled" 

    @property
    def videos(self):
        return self.series.normalizable_vids

    @property
    def is_noramlizable(self):
        return len(self.series.normalizable_vids) > 0

    @property
    def example(self):
        if self.is_noramlizable:
            evids = self.series.normalizable_vids
            evid = evids[0]
            e_norm_name = self.series.normalized_name(evid.name)
            return f"""There are a total of {len(evids)} videos to normalize. 
                       For example: {evid.name} would be normalized to {e_norm_name}"""
        else:
            return f"""Nothing to normalize in series "{self.series.name}" at this time.""" 

    def on_validated(self):    
        self.mstore.purge_cache(self.series)
        flask.flash(f"Normalized series {self.series.name}")

    @property
    def scriptage(self):
        return f"var ndtable = {self.table.scriptage}\n" + \
              """$("#Normalize_Titles input[type=submit]").click(
                  function(evt) { 
                    var vc = ndtable.rows().data()
                    var vm = vc.map(function(v) { return $(v[2]).text() })
                    for (let lname of vm.toArray()) {
                        $.ajax({url: escape(`videos/${lname}/edit`)+'?normalize', 
                                 async: false,
                                 success: function(result) { 
                                   $('#Normalize_form_results').html(result) } })
                    }
                  }) """


class SyncWithSeriesForm(SeriesForm):
    template = "sync_form.html"
    submit = SubmitField("Sync_Videos")
    legend = "Syncornize videos"

    def on_validated(self):    
        self.mstore.purge_cache(self.series)
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
        self.template_vars.update(self.table.template_vars)
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
    legend = "Or by requesting access by email"
    submit = SubmitField("Request_Access")
    email = EmailField('Email address', [validators.DataRequired(), validators.Email()])
    comments = TextAreaField(
        u'Your comments:', 
        [validators.optional(), validators.length(max=200)],
        default="Maybe give us an idea who you are and why you are requesting access...:")
    recaptcha = RecaptchaField()

    def __init__(self, lmanager):
        super().__init__()
        self.lm = lmanager

    def on_validated(self):    
        mailer = self.lm.email_adapter.mail
        rcpt = self.lm.USER_EMAIL_SENDER_EMAIL
        msg = Message("Request for Manna Access", recipients=[rcpt])
        msg.body = f"{self.email.data} says '{self.comments.data}'"
        mailer.send(msg)
        self.redirection=redirect(with_msg="Request sent....please allow a day or so for response")


class GoogleLoginForm(MannaForm):
    template = "google_login_form.html"
    legend = "Using your very own google account"
    submit = SubmitField("Google_Authorize")
    gclient = WebApplicationClient(os.environ.get("GOOGLE_CLIENT_ID"))

    def __init__(self, lmanager):
        super().__init__()
        self.lm = lmanager
        if 'code' in flask.request.args:
            self.redirection=redirect(
                self.process_google_auth(
                    flask.request.url, 
                    flask.request.base_url, 
                    flask.request.args.get('code')))


    def on_validated(self):
        # Use gclient to construct the request for Google login and provide
        # scopes that let you retrieve user's profile from Google
        next_url = flask.request.args.get('next', f"{flask.request.root_path}/")
        next_url = next_url.partition(flask.request.root_path)[2]
        request_uri = self.gclient.prepare_request_uri(
            self.google_provider_cfg("authorization_endpoint"),
            redirect_uri=flask.request.base_url, #flask.url_for("google_auth", _external=True),
            scope=["openid", "email", "profile"],
            state=next_url)
        self.redirection=redirect(request_uri)

    def google_provider_cfg(self, key):
        GOOGLE_OPEN_ID_URL="https://accounts.google.com/.well-known/openid-configuration"
        if not hasattr(self, '_gpc'):
            self._gpc = requests.get(GOOGLE_OPEN_ID_URL).json()
        return self._gpc[key]

    def process_google_auth(self, auth_url, redir_url, gcode):
        # Get authorization code Google sent back to you
        token_url, headers, body = self.gclient.prepare_token_request(
            self.google_provider_cfg("token_endpoint"),
            authorization_response=auth_url,
            redirect_url=redir_url, 
            code=gcode)
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(self.gclient.client_id, os.getenv('GOOGLE_CLIENT_SECRET')),)
        # Parse the tokens!
        self.gclient.parse_request_body_response(json.dumps(token_response.json()))
        # Now that you have tokens (yay) let's find and hit the URL
        # from Google that gives you the user's profile information,
        # including their Google profile image and email
        userinfo_endpoint = self.google_provider_cfg("userinfo_endpoint")
        uri, headers, body = self.gclient.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        # The user authenticated with Google, authorized your
        # app, and now you've verified their email through Google!
        if userinfo_response.json().get("email_verified"):
            unique_id = userinfo_response.json()["sub"]
            users_email = userinfo_response.json()["email"]
            picture = userinfo_response.json()["picture"]
            #users_name = userinfo_response.json()["given_name"]
        else:
            return "User email not available or not verified by Google.", 400
        # Create a user in your mdb with the information provided by Google
        user = User.query.filter_by(email=users_email).first()
        if not user:
            user = User(email=users_email, active=(User.query.count() <= 1))
            mdb.session.add(user)
            mdb.session.commit()

        if user.is_active: # Begin user session by logging the user in
            self.lm.login(user)
            flask.flash(f"{user.email} is now logged in.")
            return f"{flask.request.url_root}{flask.request.args.get('state')}"
        else: #An entry for the user now exists but needs to be made active before first use.
            flask.flash(f"Waiting for {user.name} confirmation.")
            return flask.url_for("list_latest")


class LoginUserForm(InviteUserForm):
    template = "login_form.html"
    legend = "Using a previously established account"
    password = PasswordField("Password", [validators.DataRequired()])
    recaptcha = RecaptchaField()
    submit = SubmitField("Login")

    def on_validated(self):
        safe_next_url = self.lm._get_safe_next_url('next', self.lm.USER_AFTER_LOGIN_ENDPOINT)
        user, user_email = self.lm.db_manager.get_user_and_user_email_by_email(self.email.data)
        if user:
            self.redirection=self.lm._do_login_user(user, safe_next_url)

