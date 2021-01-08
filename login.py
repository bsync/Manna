import flask, flask_login, os, pathlib, requests, json
import mongo, pages, mannatags
import dominate.tags as tags
from flask import redirect, url_for
from oauthlib.oauth2 import WebApplicationClient
from urllib.parse import unquote, urlsplit
try:
    import passcheck
except:
    passcheck = False

lm = flask_login.LoginManager()
lbp = flask.Blueprint('loginbp', __name__)
required = flask_login.login_required
gclient = WebApplicationClient(os.environ.get("GOOGLE_CLIENT_ID"))

def init_flask(app):
    lm.init_app(app)
    lm.login_view = 'loginbp.login'
    app.register_blueprint(lbp)
    return lm

@lbp.route('/new_user')
def new_user():
    pg = pages.MannaPage("Registration")
    pg.integrate(RegisterForm("Register to access more lessons!"))
    return pg

@lbp.route('/confirm_users', methods=['GET', 'POST'])
def confirm_users():
    pg = pages.MannaPage("Registration Confirmation")
    rc_form = pg.integrate(ConfirmRegistrationForm(mongo.User.objects))
    if rc_form.id in flask.request.form:
        for user in rc_form.selected_users:
            user.is_active = rc_form.operation == "Register"
            user.save()
        rc_form.utable.refresh(mongo.User.objects)
    return pg

@lbp.route('/register', methods=['POST'])
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

_gpc = None
GOOGLE_OPEN_ID_URL="https://accounts.google.com/.well-known/openid-configuration"
def google_provider_cfg(key):
    global _gpc
    if not _gpc:
        _gpc = requests.get(GOOGLE_OPEN_ID_URL).json()
    return _gpc[key]

@lbp.route("/login", methods=['GET', 'POST'])
def login():
    if flask_login.current_user.is_authenticated:
        return redirect(url_for("list_latest"))
    pg = pages.MannaPage("Authorization Required...")
    lform = pg.integrate(LoginForm(flask.request.args.get('next', "")))
    if lform.id in flask.request.form:
        if lform.is_validated:
            flask.session[unquote(lform.target)]=True
            flask_login.login_user(PageUser(), remember=False)
            return redirect(lform.target)
        else:
            # Use library to construct the request for Google login and provide
            # scopes that let you retrieve user's profile from Google
            request_uri = gclient.prepare_request_uri(
                google_provider_cfg("authorization_endpoint"),
                redirect_uri=url_for("loginbp.google_auth", _external=True),
                scope=["openid", "email", "profile"],
                state=lform.target)
            return redirect(request_uri)
    return pg

@lbp.route("/logout")
def logout():
    flask_login.logout_user()
    return redirect(url_for("list_latest"))

@lbp.route("/login/google_auth")
def google_auth():
    # Get authorization code Google sent back to you
    token_url, headers, body = gclient.prepare_token_request(
        google_provider_cfg("token_endpoint"),
        authorization_response=flask.request.url,
        redirect_url=flask.request.base_url,
        code=flask.request.args.get("code"))
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
    user = mongo.User.objects(id_=unique_id).first()
    if not user:
        user = mongo.User(id_=unique_id, 
                          name=users_name, 
                          email=users_email, 
                          profile_pic=picture,
                          is_active=(len(mongo.User.objects) == 0))
        user.save()

    if user.is_active: # Begin user session by logging the user in
        flask_login.login_user(user)
        hurl = flask.request.url_root.partition(flask.request.script_root)[0]
        return redirect(f"{hurl}{flask.request.args.get('state')}")
    else: #An entry for the user now exists but needs to be made active before first use.
        flask.flash(f"Waiting for {user.name} confirmation.")
        return redirect(url_for("list_latest"))

class PageUser(flask_login.UserMixin): 
    def get_id(self): 
        return 0

@lm.user_loader
def load_user(user_id):
    mongo_user =  mongo.User.objects(id_=user_id).first()
    if mongo_user:
        return mongo_user
    if flask.session.get(unquote(flask.request.script_root + flask.request.path)):
        return PageUser()
    if flask.session.get(''):
        return PageUser()


class LoginForm(mannatags.SubmissionForm):
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
            self.utable = self.addTable(mannatags.UserTable(users))
            tags.input(id=f"{self.submit_id}2", 
                       type='submit', 
                       name='submit_button',
                       _class='submit_button',
                       value="Unregister",
                       style="clear: both; width: 100%; margin-top: 20px;")
        self.on_ready_scriptage = self.utable.on_ready_scriptage

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
        
