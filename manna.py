import flask, flask_login, pages
from werkzeug.exceptions import HTTPException

bp = flask.Blueprint('mannabp', __name__, 
                     url_prefix='/manna', 
                     static_folder='static')

@bp.record
def record(state):
    lm = flask_login.LoginManager(state.app)
    lm.login_view = 'mannabp.auth'
    pages.init_flask(state.app, lm) 

@bp.route('auth', methods=['GET', 'POST'])
def auth():
    target = flask.request.args.get('next')
    return pages.AuthenticationPage(target).response

@bp.route("/")
def latest():
    return pages.LatestPage(10).response

@bp.route("/roku")
def roku():
    print("TODO: update roku showcase")
    return pages.LatestPage(10).feed

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

