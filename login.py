import flask, os, requests, json
import dominate.tags as tags
import flask_user, flask_login
import pages
from flask import redirect, url_for
from oauthlib.oauth2 import WebApplicationClient
from urllib.parse import unquote, quote, urlsplit
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_wtf import FlaskForm
from dominate.util import raw

gclient = WebApplicationClient(os.environ.get("GOOGLE_CLIENT_ID"))
_gpc = None
GOOGLE_OPEN_ID_URL="https://accounts.google.com/.well-known/openid-configuration"
def google_provider_cfg(key):
    global _gpc
    if not _gpc:
        _gpc = requests.get(GOOGLE_OPEN_ID_URL).json()
    return _gpc[key]


class Login(object):
    def __init__(self, app):
        db = SQLAlchemy(app)

        # Define the User document.
        class User(db.Model, flask_user.UserMixin):
            __tablename__ = 'users'
            id = db.Column(db.Integer, primary_key=True)
            active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

            # User authentication information. The collation='NOCASE' is required
            # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
            email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
            email_confirmed_at = db.Column(db.DateTime())
            password = db.Column(db.String(255), nullable=False, server_default='')

            # User information
            first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
            last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
            username = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')

            # Define the relationship to Role via UserRoles
            roles = db.relationship('Role', secondary='user_roles')

        # Define the Role data-model
        class Role(db.Model):
            __tablename__ = 'roles'
            id = db.Column(db.Integer(), primary_key=True)
            name = db.Column(db.String(50), unique=True)

        # Define the UserRoles association table
        class UserRoles(db.Model):
            __tablename__ = 'user_roles'
            id = db.Column(db.Integer(), primary_key=True)
            user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
            role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

        # Setup Flask-User and specify the User data-model
        self.user_manager = flask_user.UserManager(app, db, User)

        db.create_all()

        # Create 'admin@example.com' user with 'Admin' and 'Agent' roles
        if not User.query.filter(User.email == 'james.horine@gmail.com').first():
            user = User(
                username='admin',
                email='james.horine@gmail.com',
                email_confirmed_at=datetime.utcnow(),
                #password=user_manager.hash_password('Password1'),
            )
            user.roles.append(Role(name='Admin'))
            user.roles.append(Role(name='Agent'))
            db.session.add(user)
            db.session.commit()

        # Customize the password manager
        #class LoginPassManager(PasswordManager):
        #    pass
        #self.user_manager.password_manager = LoginPassManager(app, 'bcrypt')
        self.db = db
        self.User = User

    @property 
    def required(self):
        return flask_user.login_required

    def googleLoginForm(self, target_url):
        return GoogleLoginForm(self.db, self.User, target_url)

    def loginForm(self, target_url):
        return LoginForm(self.db, self.User, target_url)

    def register_view(self, func):
        self.user_manager.login_view = func

    def new_user():
        pg = pages.MannaPage("Registration")
        nuf = pg.integrate(RegisterForm("Register to access more lessons!"))
        if nuf.id in flask.request.form:
            return redirect('edit_confirm_users')

        return pg

    def edit_confirm_users():
        pg = pages.MannaPage("Registration Confirmation")
        rc_form = pg.integrate(ConfirmRegistrationForm(mongo.User.objects))
        if rc_form.id in flask.request.form:
            for user in rc_form.selected_users:
                user.is_active = rc_form.operation == "Register"
                user.save()
            rc_form.utable.refresh(mongo.User.objects)
        return pg

    def register():
        form = flask.request.form
        username = form['user']
        user = mongo.User.objects(name=username).first()
        if not user:
            user = mongo.User(name=username, 
                              email=users_email, 
                              profile_pic=picture,
                              is_active=(len(mongo.User.objects) == 0))
            flask.flash('Congratulations, you are now a registered user!')
        return redirect('login')


    def logout():
        flask_login.logout_user()
        return redirect(url_for("list_latest"))


class LoginForm(flask_user.forms.LoginForm):
    def __init__(self, target_url):
        super().__init__()
        if self.id in flask.request.form:
            if self.is_validated:
                flask.session[unquote(target_url)]=True
                flask_login.login_user(PageUser(), remember=False)
                self.html = redirect(target_url)
        else:
            with tags.form() as self.html:
                tags.input()(self.password)
            

class GoogleLoginForm(FlaskForm):
    template = "login.html"
    def __init__(self, db, UserCls, target):
        super().__init__()
        self.db = db
        self.UserCls = UserCls
        self.template_vars = dict(login_form=self)
        if self.validate_on_submit():
            # Use library to construct the request for Google login and provide
            # scopes that let you retrieve user's profile from Google
            rd_url = flask.request.url_root.strip('/') + flask.request.path
            request_uri = gclient.prepare_request_uri(
                google_provider_cfg("authorization_endpoint"),
                redirect_uri=rd_url, #url_for("google_auth", _external=True),
                scope=["openid", "email", "profile"],
                state=target)
            self.redirect = redirect(request_uri)
        elif 'code' in flask.request.args:
            self.redirect = redirect(self.process_auth(
                                    flask.request.url,
                                    flask.request.base_url,
                                    flask.request.args.get('code')),)

    def process_auth(self, auth_url, redir_url, gcode):
        # Get authorization code Google sent back to you
        token_url, headers, body = gclient.prepare_token_request(
            google_provider_cfg("token_endpoint"),
            authorization_response=auth_url,
            redirect_url=redir_url, 
            code=gcode)
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(gclient.client_id, os.getenv('GOOGLE_CLIENT_SECRET')),)
        # Parse the tokens!
        gclient.parse_request_body_response(json.dumps(token_response.json()))
        # Now that you have tokens (yay) let's find and hit the URL
        # from Google that gives you the user's profile information,
        # including their Google profile image and email
        userinfo_endpoint = google_provider_cfg("userinfo_endpoint")
        uri, headers, body = gclient.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        # The user authenticated with Google, authorized your
        # app, and now you've verified their email through Google!
        if userinfo_response.json().get("email_verified"):
            unique_id = userinfo_response.json()["sub"]
            users_email = userinfo_response.json()["email"]
            picture = userinfo_response.json()["picture"]
            users_name = userinfo_response.json()["given_name"]
        else:
            return "User email not available or not verified by Google.", 400
        # Create a user in your db with the information provided by Google
        user = self.UserCls.query.filter_by(email=users_email).first()
        if not user:
            user = self.UserCls(username=users_name, 
                                email=users_email, 
                                active=(self.UserCls.query.count() <= 1))
            self.db.session.add(user)
            self.db.session.commit()

        if user.is_active: # Begin user session by logging the user in
            flask_login.login_user(user)
            return f"{flask.request.url_root}{flask.request.args.get('state')}"
        else: #An entry for the user now exists but needs to be made active before first use.
            flask.flash(f"Waiting for {user.name} confirmation.")
            return url_for("list_latest")


import mannatags
class OldLoginForm(mannatags.SubmissionForm):
    def __init__(self, target_in=""):    
        super().__init__(f"Login to access {target_in}")
        self.target = target_in
        self.username = "guest"
        self._passcheck = passcheck and passcheck.handles(self.target)
        if self._passcheck:
            with self.content:
                #tags.label("Username:") 
                #tags.input(id="username") 
                tags.label("Password:") 
                tags.input(id="password", name="password", type="password") 
        else:
            with self.content:
                tags.p("This resource requires google oauthentication. " +
                       "Click the login button below to proceed to " +
                       "google authorization page. ")

    @property
    def is_validated(self):
        if passcheck and passcheck.handles(self.target):
            return passcheck.authenticate(self.username, self.password, self.target)
        else: 
            return False


class RegisterForm(mannatags.SubmissionForm):
    pass

class ConfirmRegistrationForm(mannatags.SubmissionForm):
    def __init__(self, users, **kwargs):
        super().__init__(f"Registration...")
        self.users = users
        with self.content:
            self.utable = mannatags.UserTable(users)
            tags.input(id=f"{self.submit_id}2", 
                       type='submit', 
                       name='submit_button',
                       _class='submit_button',
                       value="Unregister",
                       style="clear: both; width: 100%; margin-top: 20px;")
        self.on_ready_scriptage = self.utable.on_ready_scriptage + f"""
            $("#{self.id}_Submit").click(function() {{
                var selrow = {self.utable.table_id}.rows( {{ selected: true }} )[0];
                var torder = {self.utable.table_id}.order()[0];
                $(":input.selection").val(selrow)
                $(":input.order").val(torder) }});""" 

    @property
    def submission_label(self):
        return "Register"

    @property
    def selected_users(self):
        vindicies = [ int(x) for x in flask.request.form['selection']]
        return [ self.users[i] for i in vindicies ]

    @property
    def operation(self):
        return flask.request.form['submit_button']
        
