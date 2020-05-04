import flask, login, pages
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = flask.Flask(__name__)
app.config.from_object("config")
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, { '/manna':app })
# Flask init the login manager and page manager
lm = login.init_flask(app)
pm = pages.init_flask(app)

@app.route('/auth', methods=['GET', 'POST'])
@lm.login_page
def auth():
    target = flask.request.args.get('next')
    return pm.AuthenticationPage(target).response

@app.route("/")
def latest():
    return pm.LatestPage(10).response

@app.route("/roku")
def roku():
    return pm.LatestPage(10).feed

@app.route("/latest/series/<series>/videos/<video>") 
def latest_player(series, video):
    return pm.VideoPlayer(series, video).response

@app.route("/series")
def catalog():
    return pm.CatalogPage().response

@app.route("/edit/series", methods=['GET', 'POST'])
@lm.login_required
def catalog_editor():
    return pm.CatalogEditorPage().response

@app.route("/edit/series/status") 
def catalog_status():
    return pm.CatalogEditorPage().status

@app.route("/series/<series>")
@lm.login_required
def series_page(series):
    return pm.SeriesPage(series).response

@app.route("/edit/series/<series>", methods=['GET', 'POST', 'DELETE'])
@lm.login_required
def series_editor_page(series):
    return pm.SeriesEditorPage(series).response

@app.route("/edit/series/<series>/status") 
def series_edit_status(series):
    return pm.SeriesEditorPage(series).status

@app.route("/series/<series>/videos/<video>") 
@lm.login_required
def video_page(series, video):
    return pm.VideoPlayer(series, vid).response

@app.route("/edit/series/<series>/videos/<video>", methods=['GET', 'POST'])
@lm.login_required
def video_editor_page(series, video):
    return pm.VideoEditor(series, video).response

@app.route("/series/<series>/audios/<audio>") 
def audio_response(series, audio):
    return pm.AudioPage(series, audio).response

@app.route("/edit/reset")
@lm.login_required
def reset():
    import mongo
    mongo.init_db()
    return flask.redirect(flask.url_for('.latest'))

@app.errorhandler(HTTPException)
def error_page(err):
    return pm.ErrorPage(err).response

