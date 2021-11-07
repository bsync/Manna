import flask, os, requests, json
import dominate.tags as tags
import flask_user, flask_login
import pages, forms
from oauthlib.oauth2 import WebApplicationClient
from urllib.parse import unquote
from datetime import datetime
from flask_wtf import FlaskForm
from models import mdb, User, Role
try:
    import passcheck
except:
    passcheck = False

class LoginManager(flask_user.UserManager):
    gclient = WebApplicationClient(os.environ.get("GOOGLE_CLIENT_ID"))
    def __init__(self, app):
        super().__init__(app, mdb, User)
        mdb.init_app(app)
        app.route("/google_login", methods=['GET', 'POST'])(self.google_login)
        app.route("/user/sign-in/edit", methods=['GET', 'POST'])(
            self.required(self.confirm_users))
        app.route("/user/sign-out/edit", methods=['GET', 'POST'])(
                lambda : flask.redirect(flask.url_for('confirm_users')))

    @property 
    def required(self):
        return flask_user.login_required

    @property
    def roles_required(self):
        return flask_user.roles_required

    def google_login(self):
        # Use library to construct the request for Google login and provide
        # scopes that let you retrieve user's profile from Google
        if 'code' not in flask.request.args:
            rd_url = flask.request.url_root.strip('/') + flask.request.path
            request_uri = self.gclient.prepare_request_uri(
                self.google_provider_cfg("authorization_endpoint"),
                redirect_uri=rd_url, #flask.url_for("google_auth", _external=True),
                scope=["openid", "email", "profile"],
                state=flask.request.form['next'].partition('/manna')[2])
            return flask.redirect(request_uri)
        else:
            return flask.redirect(
                self.process_google_auth(
                    flask.request.url, 
                    flask.request.base_url, 
                    flask.request.args.get('code')))

    def confirm_users(self):
        pg = pages.MannaPage("Registration Confirmation")
        pg.add(forms.RegistrationForm(User))
        pg.add(forms.NewUserForm())
        return pg.response

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
            flask_login.login_user(user)
            return f"{flask.request.url_root}{flask.request.args.get('state')}"
        else: #An entry for the user now exists but needs to be made active before first use.
            flask.flash(f"Waiting for {user.name} confirmation.")
            return flask.url_for("list_latest")

    def logout():
        flask_login.logout_user()
        return flask.redirect(flask.url_for("list_latest"))

