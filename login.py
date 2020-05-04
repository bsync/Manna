import flask, flask_login
from pathlib import Path

lm = flask_login.LoginManager()

def init_flask(app):
    lm.init_app(app)
    lm.login_required = flask_login.login_required
    def assign_login_view(func):
        lm.login_view = func.__name__
        return func
    lm.login_page = assign_login_view
    return lm

class PageUser(flask_login.UserMixin): 
    def get_id(self): 
        return 0

@lm.user_loader
def load_user(user_id):
    if flask.session.get(Path(flask.request.path).name):
        return PageUser()
    else:
        return None

def login_user(user_name=None):
    flask_login.login_user(PageUser())


