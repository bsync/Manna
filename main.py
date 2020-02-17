import flask, flask_login, sys
import pages, vimongo
from werkzeug.exceptions import HTTPException
from urllib.parse import unquote
from dotenv import load_dotenv; load_dotenv()

def create_app(config=None):
    app = flask.Flask(__name__, static_url_path="/manna/static")
    app.config.from_object("config")
    print(f"FLask running in {app.env} mode!")
    vimongo.mdb.init_app(app)
    lm = flask_login.LoginManager(app)
    lm.login_view = 'auth'

    class PageUser(flask_login.UserMixin): 
        def get_id(self): 
            return 0

    @lm.user_loader
    def load_user(user_id):
        if flask.session.get(flask.request.path):
            return PageUser()
        else:
            return None

    @app.route('/manna/vsync')
    def vsync():
        return flask.Response(vimongo.status)

    @app.route('/manna/auth', methods=['GET', 'POST'])
    def auth():
        target = flask.request.args.get('next')
        lp = pages.PasswordPage(target)
        if lp.passes:
            flask_login.login_user(PageUser())
            flask.session[unquote(target)]=True
            return flask.redirect(target)
        return str(lp)

    @app.route("/manna/")
    def latest_vids_page():
        vids = vimongo.VideoRecord.latest(10)
        return str(pages.LatestLessons(vids))

    @app.route("/manna/latest/<video>") 
    def latest_page(video):
        video = vimongo.VideoRecord.objects(uri__contains=video).first()
        return str(pages.VideoPlayer(video))

    @app.route("/manna/albums")
    def catalog_page():
        return str(pages.Catalog(vimongo.AlbumRecord))

    @app.route("/manna/albums/edit", methods=['GET', 'POST'])
    @flask_login.login_required
    def catalog_edit_page():
        return str(pages.Catalog(vimongo.AlbumRecord, edit=True))

    @app.route("/manna/albums/<album>")
    @flask_login.login_required
    def series_page(album):
        alb = vimongo.AlbumRecord.named(album)
        return str(pages.Series(alb))

    @app.route("/manna/albums/<album>/edit", methods=['GET', 'POST'])
    @flask_login.login_required
    def series_edit_page(album):
        alb = vimongo.AlbumRecord.named(album)
        return str(pages.Series(alb, edit=True))

    @app.route("/manna/videos/<video>") 
    @flask_login.login_required
    def video_page(video):
        return str(pages.VideoPlayer(video))

    @app.route("/manna/albums/<album>/audios/<audio>") 
    def audio_response(album, audio):
        def generate_mp3():
            yield 'This feature is coming soon!'
        return flask.Response(generate_mp3(), mimetype="text/plain")

    @app.errorhandler(HTTPException)
    def error_page(err):
        return str(pages.ErrorPage(err.original_exception))

    return app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
