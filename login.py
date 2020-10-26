import flask, flask_login, os, pathlib, requests, json
import mongo, pages, forms
from flask import redirect, url_for
from oauthlib.oauth2 import WebApplicationClient
try:
    import passcheck
except:
    passcheck = None

gid = os.getenv('GOOGLE_CLIENT_ID')
client = WebApplicationClient(gid)
lm = flask_login.LoginManager()
lbp = flask.Blueprint('loginbp', __name__)
required = flask_login.login_required

def init_flask(app):
    lm.init_app(app)
    lm.login_view = 'loginbp.login'
    app.register_blueprint(lbp)
    return lm

@lbp.route('/new_user', methods=['GET'])
def new_user():
    pg = pages.MannaPage("Registration")
    pg.integrate(
        forms.RegisterForm(
            f"Register to access more lessons",
            url_for('register')))
    return pg.response

@lbp.route('/register', methods=['POST'])
def register():
    import pdb; pdb.set_trace()
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

_google_provider_cfg = None
def google_provider_cfg(key):
    global _google_provider_cfg
    if not _google_provider_cfg:
        gdu = os.getenv('GOOGLE_DISCOVERY_URL')
        _google_provider_cfg = requests.get(gdu).json()
    return _google_provider_cfg[key]

@lbp.route("/login")
def login():
    if flask_login.current_user.is_authenticated:
        return redirect(url_for("latest"))
    nxt = flask.request.args['next']
    if passcheck and passcheck.handles(nxt):
        pg = pages.MannaPage("Authorization Required...")
        pg.integrate(
            forms.LoginForm(
                f"Login to access {nxt}",
                url_for('loginbp.auth', target=nxt)))
        return pg

    # Find out what URL to hit for Google login
    authorization_endpoint = google_provider_cfg("authorization_endpoint")
    # Any editable pages require more robust login using google oauth
    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    return redirect(
        client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=url_for("loginbp.google_auth", _external=True),
            scope=["openid", "email", "profile"],
            state=nxt))

@lbp.route("/logout")
def logout():
    flask_login.logout_user()
    return redirect('show_catalog_page')

@lbp.route("/login/google_auth")
def google_auth():
    # Get authorization code Google sent back to you
    token_endpoint = google_provider_cfg("token_endpoint")
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=flask.request.url,
        redirect_url=flask.request.base_url,
        code=flask.request.args.get("code"))
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(gid, os.getenv('GOOGLE_CLIENT_SECRET')),)
    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))
    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg("userinfo_endpoint")
    uri, headers, body = client.add_token(userinfo_endpoint)
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
        return redirect(f"{flask.request.url_root}{flask.request.args.get('state')}")
    else: #An entry for the user now exists but needs to be made active before first use.
        return redirect(url_for("latest"))

@lbp.route('/auth', methods=['POST'])
def auth():
    target = flask.request.args['target']
    form = flask.request.form
    username = form['user']
    guessword = form['guessword']
    if passcheck.authenticate(username, guessword, target):
        flask.session[pathlib.Path(target).name]=True
        flask_login.login_user(PageUser(), remember=False)
        return redirect(target)
    else:
        flask.flash('Invalid username or password.')
        return redirect(url_for('loginbp.login'))

class PageUser(flask_login.UserMixin): 
    def get_id(self): 
        return 0

@lm.user_loader
def load_user(user_id):
    if flask.session.get(pathlib.Path(flask.request.path).name):
        return PageUser()
    else:
        return mongo.User.objects(id_=user_id).first()
