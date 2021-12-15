import os
import pages, forms
import flask_user, flask_login
from models import mdb, User, UserInvitation
from flask import redirect, request, flash
from flask_wtf import FlaskForm
from urllib.parse import quote, unquote    # Python 3
try:
    import passcheck
except:
    passcheck = False

class UserLoginManager(flask_user.UserManager):
    def __init__(self, app):
        super().__init__(app, mdb, User, UserInvitationClass=UserInvitation)
        mdb.init_app(app)
        self.app = app
        self.Users = User
        rr = self.roles_required('Admin')(self.manage_registrations)
        app.route("/user/sign-in/edit", methods=['GET', 'POST'])(rr)
        app.route("/user/sign-out/edit", methods=['GET', 'POST'])(rr)

    @property 
    def required(self):
        return flask_user.login_required

    @property
    def roles_required(self):
        return flask_user.roles_required

    def manage_registrations(self):
        return pages.RegistrationPage(self).response

    def register_view(self):
        #import pdb; pdb.set_trace()
        return super().register_view()

    def login_view(self):
        return pages.LoginPage(self).response

    def login(self, user):
        flask_login.login_user(user)

    def logout(self):
        flask_login.logout_user()
        return flask.redirect(flask.url_for("list_latest"))

    def unauthenticated_view(self):
        """ Prepare a Flash message and redirect to USER_UNAUTHENTICATED_ENDPOINT"""
        # Prepare Flash message
        flash(f"You must be signed in to access '{request.path.rpartition('/')[2]}'", 'error')
        # Redirect to USER_UNAUTHORIZED_ENDPOINT
        safe_next_url = self.make_safe_url(request.url)
        return redirect(self._endpoint_url(self.USER_UNAUTHENTICATED_ENDPOINT)+'?next='+quote(safe_next_url))
