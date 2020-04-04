import os, flask, flask_login, pages
from werkzeug.exceptions import HTTPException
from urllib.parse import unquote

bp = flask.Blueprint('mannabp', __name__, 
                     url_prefix='/manna', 
                     static_folder='static')

class PageUser(flask_login.UserMixin): 
    def get_id(self): 
        return 0

def load_user(user_id):
    if flask.session.get(flask.request.path):
        return PageUser()
    else:
        return None

@bp.record
def record(state):
    lm = flask_login.LoginManager(state.app)
    lm.user_loader(load_user)
    lm.login_view = 'mannabp.auth'
    pages.init_app(state.app) 

@bp.route('auth', methods=['GET', 'POST'])
def auth():
    target = flask.request.args.get('next')
    lp = pages.PasswordPage(target)
    if lp.passes:
        flask_login.login_user(PageUser())
        flask.session[unquote(target)]=True
        return flask.redirect(target)
    return lp.response

@bp.route("/")
def latest():
    return pages.LatestPage(10).response

@bp.route("/latest/albums/<album>/videos/<video>") 
def latest_player(album, video):
    return pages.VideoPlayer(album, video).response

@bp.route("/albums")
def catalog():
    return pages.CatalogPage().response

@bp.route("/edit/albums", methods=['GET', 'POST'])
@flask_login.login_required
def catalog_editor():
    return pages.CatalogEditorPage().response

@bp.route("/edit/albums/status") 
def catalog_status():
    return pages.CatalogEditorPage().status

@bp.route("/albums/<album>")
@flask_login.login_required
def series_page(album):
    return pages.SeriesPage(album).response

@bp.route("/edit/albums/<album>", methods=['GET', 'POST', 'DELETE'])
@flask_login.login_required
def series_editor_page(album):
    return pages.SeriesEditorPage(album).response

@bp.route("/edit/albums/<album>/status") 
def series_edit_status(album):
    return pages.SeriesEditorPage(album).status

@bp.route("/albums/<album>/videos/<video>") 
@flask_login.login_required
def video_page(album, video):
    return pages.VideoPlayer(album, vid).response

@bp.route("/edit/albums/<album>/videos/<video>", methods=['GET', 'POST'])
@flask_login.login_required
def video_editor_page(album, video):
    return pages.VideoEditor(album, video).response

@bp.route("/albums/<album>/audios/<audio>") 
def audio_response(album, audio):
    return pages.AudioPage(album, audio).response

@bp.errorhandler(HTTPException)
def error_page(err):
    return pages.ErrorPage(err).response

