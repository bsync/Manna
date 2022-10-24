import flask, flask_login, json
import requests as bg_requests
from oauthlib.oauth2 import WebApplicationClient
from flask_principal import Principal, Permission, RoleNeed, Identity, UserNeed
from flask_principal import AnonymousIdentity, identity_changed, identity_loaded
from flask_login import current_user
from flask_mail import Message
from .database import Datastore

class Mannager(flask_login.LoginManager):
    admin_permission = Permission(RoleNeed('Admin'))
    def __init__(self, app, view="login", mailer=None):
        super().__init__(app)
        self.login_view = view
        self.mailer= mailer
        self.datastore = Datastore(app)
        self.principal = Principal(app)
        self.config = app.config
        with app.app_context():
            if not self.datastore.find_role(name="Admin"):
                self.datastore.create_role(name="Admin")
            if not self.admin:
                self.datastore.create_user(
                    username='admin', 
                    email=self.config.get('ADMIN_EMAIL', 'james.horine@gmail.com'), 
                    desc="Oauth only default admin account",
                    active=True,
                    roles=["Admin"])
            if self.config.get('GUEST_EMAIL', False):
                if not self.guest:
                    self.datastore.create_user(
                        username='guest', 
                        email=self.config.get('GUEST_EMAIL'), 
                        desc="Guest account if you know the guest password.",
                        active=True,
                        password=self.config.get('GUEST_PASS', ''),)

        self.gclient_id = self.config.get('G_CLIENT_ID', None)
        self.gclient_secret = self.config.get('G_CLIENT_SECRET', None)
        self.gclient = WebApplicationClient(self.gclient_id)
        self.gprov = bg_requests.get("https://accounts.google.com/.well-known/openid-configuration").json()
    
        self.user_loader(self.load_user)
        identity_loaded.connect_via(app)(self.on_identity_loaded)
        self.login_required = flask_login.login_required

    def load_user(self, userid):
        return self.datastore.find_user(id=userid)

    @property
    def admin(self): 
        return self.datastore.find_user(email="james.horine@gmail.com")
    
    @property
    def guest(self): 
        return self.datastore.find_user(email=self.config.get('GUEST_EMAIL', 'guest@un.known'))

    @property
    def admin_required(self):
        return self.admin_permission.require()

    def login_via_email(self, email, password):
        user = self.datastore.find_user(email=email)
        if user and user.password == password:
            return self.login(
                user, 
                flask.request.values.get('next', flask.url_for('show_recent')))
        else:
            flask.flash(f"Login failed for {email}.")
            return flask.redirect(flask.url_for('show_recent'))

    def login_via_google(self):
        if 'google_callback' in flask.request.args:
            return self.google_callback()
        flask.session['next_url'] = flask.request.values.get('next', flask.url_for('show_recent'))
        return flask.redirect(self.gclient.prepare_request_uri(
            self.gprov["authorization_endpoint"],
            redirect_uri=flask.request.base_url + "?google_callback",
            scope=["openid", "email", "profile"],))

    def google_callback(self):
        code = flask.request.args.get("code")
        token_url, headers, body = self.gclient.prepare_token_request(
            self.gprov['token_endpoint'],
            authorization_response=flask.request.url,
            redirect_url=flask.request.base_url + "?google_callback",
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
        else:
            return "User email not available or not verified by Google.", 400
        # Create a user in your db with the information provided by Google
        user = self.datastore.find_user(email=users_email)
        if not user:
            user = self.datastore.create_user( email=users_email, active=False)

        if user.is_active: # Begin user session by logging the user in
            flask.flash(f"{user.email} is now logged in.")
            return self.login(user, flask.session['next_url'])
        else: #An entry for the user now exists but needs to be made active before first use.
            flask.flash(f"Waiting for {user.username} confirmation.")
            return flask.redirect(flask.url_for("show_recent"))

    def login(self, user, next_url):
        flask_login.login_user(user)
        identity_changed.send(
            flask.current_app._get_current_object(),
            identity=Identity(user.id))
        return flask.redirect(next_url)

    def on_identity_loaded(self, sender, identity):
        # Set the identity user object
        identity.user = current_user

        # Add the UserNeed to the identity
        if hasattr(current_user, 'id'):
            identity.provides.add(UserNeed(current_user.id))

        # Assuming the User model has a list of roles, update the
        # identity with the roles that the user provides
        if hasattr(current_user, 'roles'):
            for role in current_user.roles:
                identity.provides.add(RoleNeed(role.name))
    
    def request_access(self, email, comments):    
        msg = Message("Request for Manna Access", 
                recipients=[self.mailer.app.config.get('MAIL_USERNAME', '')])
        msg.body = f"{email} says '{comments}'"
        self.mailer.send(msg)
        return flask.redirect(with_msg="Request sent....please allow a day or so for response")

    def invite_access(self, email, comments):
        if self.datastore.find_user(email=email):
            return flask.redirect(with_msg=f"{email} already exists in the user database...try something else!")
        else:
            self.datastore.create_user(email=email, desc=comments, active=False,)
            return flask.redirect(with_msg=f"{email} added to the user database...waiting for confirmation!")

    def register_user(self, su):
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
                self.session.delete(su)
            self.session.commit()
        self.redirection=redirect(with_msg=f"{self.operation} completed!")

    def logout(self):
        flask.flash(f"{current_user.username} logged out.")
        identity_changed.send(
            flask.current_app._get_current_object(),
            identity=AnonymousIdentity())
        flask_login.logout_user()
