import pages
import flask, flask_user, flask_login
import requests as bg_requests
import json
from flask import request, session
from models import mdb, User, UserInvitation
from flask_wtf import FlaskForm
from urllib.parse import quote, unquote    # Python 3
from oauthlib.oauth2 import WebApplicationClient
from datetime import datetime
try:
    import passcheck
except:
    passcheck = False

class UserLoginManager(flask_user.UserManager):
    def __init__(self, app):
        super().__init__(app, mdb, User, UserInvitationClass=UserInvitation)
        mdb.init_app(app)
        self.app = app
        self.gclient_id = app.config.get('G_CLIENT_ID', None)
        self.gclient_secret = app.config.get('G_CLIENT_SECRET', None)
        self.gclient = WebApplicationClient(self.gclient_id)
        self.gprov = bg_requests.get("https://accounts.google.com/.well-known/openid-configuration").json()
        self.Users = User
        rr = self.roles_required('Admin')(self.manage_registrations)
        app.route("/user/sign-in/edit", methods=['GET', 'POST'])(rr)
        app.route("/user/sign-out/edit", methods=['GET', 'POST'])(rr)
        app.route("/user/sign-in/google_callback")(self.google_callback) 

    @property 
    def login_required(self):
        return flask_user.login_required

    @property
    def roles_required(self):
        return flask_user.roles_required

    @property
    def guest(self):
        if 'GUEST_EMAIL' in self.app.config:
            return User.query.filter_by(email=self.app.config['GUEST_EMAIL']).first()
        else:
            return None

    def manage_registrations(self):
        return pages.RegistrationPage(self).response

    def register_view(self):
        return super().register_view()

    def login_view(self):
        pg = pages.LoginPage(self)
        if pg.redirection:
            return pg.redirection
        else:
            return flask.render_template("login_form.html", page=pg)

    def login(self, user):
        flask_login.login_user(user)

    def logout(self):
        flask_login.logout_user()
        return flask.redirect(flask.url_for("list_recent"))

    def unauthenticated_view(self):
        """ Prepare a Flash message and redirect to USER_UNAUTHENTICATED_ENDPOINT"""
        # Prepare Flash message
        flask.flash(f"You must be signed in to access '{request.path}'", 'error')
        # Redirect to USER_UNAUTHORIZED_ENDPOINT
        return flask.redirect(
            self._endpoint_url(
                self.USER_UNAUTHENTICATED_ENDPOINT)+'?next='+quote(
                    self.make_safe_url(request.url)))

    def login_via_email(self, email, password):
        user = self.db_manager.get_user_and_user_email_by_email(email)[0] 
        if user:
            next_url = self._get_safe_next_url('next', self.USER_AFTER_LOGIN_ENDPOINT)
            return self._do_login_user(user, next_url)

    def login_via_google(self):
        session['next_url'] = self._get_safe_next_url('next', self.USER_AFTER_LOGIN_ENDPOINT)
        return flask.redirect(self.gclient.prepare_request_uri(
            self.gprov["authorization_endpoint"],
            redirect_uri=request.base_url + "/google_callback",
            scope=["openid", "email", "profile"],))

    def google_callback(self):
        code = request.args.get("code")

        token_url, headers, body = self.gclient.prepare_token_request(
            self.gprov['token_endpoint'],
            authorization_response=request.url,
            redirect_url=request.base_url,
            code=code)

        token_response = bg_requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(self.gclient_id, self.gclient_secret),)

		# Parse the tokens!
        self.gclient.parse_request_body_response(json.dumps(token_response.json()))

        uri, headers, body = self.gclient.add_token(self.gprov["userinfo_endpoint"])
        userinfo_response = bg_requests.get(uri, headers=headers, data=body)

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
            flask.flash(f"{user.email} is now logged in.")
            return self._do_login_user(user, session['next_url'])
            #return f"{request.url_root}{request.args.get('state')}"
        else: #An entry for the user now exists but needs to be made active before first use.
            flask.flash(f"Waiting for {user.name} confirmation.")
            return flask.url_for("list_recent")
