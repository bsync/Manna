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
        return lp.response

    @app.route("/manna/")
    def latest_vids_page():
        vids = vimongo.Video.latest(10)
        return pages.LatestLessonsPage(vids).response

    @app.route("/manna/latest/albums/<album>/videos/<video>") 
    def latest_video_page(album, video):
        import pdb; pdb.set_trace()
        vid = vimongo.VideoSeries.named(album).get_video_named(video)
        return pages.VideoPlayer(vid).response

    @app.route("/manna/edit/latest/albums/<album>/videos/<video>") 
    def latest_video_editor_page(album, video):
        return flask.redirect(
                flask.url_for('video_editor_page', album=album, video=video))

    @app.route("/manna/albums")
    def catalog_page():
        return pages.CatalogPage(vimongo.VideoSeries).response

    @app.route("/manna/edit/albums", methods=['GET', 'POST'])
    @flask_login.login_required
    def catalog_editor_page():
        return pages.CatalogEditorPage(vimongo.VideoSeries).response

    @app.route("/manna/albums/<album>")
    @flask_login.login_required
    def series_page(album):
        alb = vimongo.VideoSeries.named(album)
        return pages.SeriesPage(alb).response

    @app.route("/manna/edit/albums/<album>", methods=['GET', 'POST', 'DELETE'])
    @flask_login.login_required
    def series_editor_page(album):
        alb = vimongo.VideoSeries.named(album)
        return pages.SeriesEditorPage(alb).response

    @app.route("/manna/albums/<album>/videos/<video>") 
    @flask_login.login_required
    def video_page(album, video):
        vid = vimongo.VideoSeries.named(album).get_video_named(video)
        return pages.VideoPlayer(vid).response

    @app.route("/manna/edit/albums/<album>/videos/<video>", methods=['GET', 'POST'])
    @flask_login.login_required
    def video_editor_page(album, video):
        vid = vimongo.VideoSeries.named(album).get_video_named(video)
        return pages.VideoEditor(vid).response

    @app.route("/manna/albums/<album>/audios/<audio>") 
    def audio_response(album, audio):
        def generate_mp3():
            yield 'This feature is coming soon!'
        return flask.Response(generate_mp3(), mimetype="text/plain")

    @app.errorhandler(HTTPException)
    def error_page(err):
        return pages.ErrorPage(err.description).response

    return app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
