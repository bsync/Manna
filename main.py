import flask, flask_login, sys
import pages, vimongo
from werkzeug.exceptions import HTTPException
from urllib.parse import unquote
from dotenv import load_dotenv 
try:
    import passcheck
    passcheck("fail early", "if passcheck doesn't work")
except Exception as e:
    passcheck = None

load_dotenv()

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

    @app.route('/manna/auth', methods=['GET', 'POST'])
    def auth():
        target = flask.request.args.get('next')
        if passcheck is None: 
            flask_login.login_user(PageUser())
            flask.session[unquote(target)]=True
            return flask.redirect(target)
        lp = pages.PasswordPage(target)
        if lp.hasValidSubmission:
            if passcheck(lp.target, lp.guess):
                flask_login.login_user(PageUser())
                flask.session[unquote(lp.target)]=True
                return flask.redirect(lp.target)
            else:
                return str(lp)
        else:
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
        return str(pages.Catalog(vimongo.AlbumRecord.objects))

    @app.route("/manna/albums/edit", methods=['GET', 'POST'])
    @flask_login.login_required
    def catalog_edit_page():
        cat = pages.Catalog(vimongo.AlbumRecord.objects, edit=True)
        if cat.hasValidSubmission:
            try:
                ar = vimongo.AlbumRecord.addAlbum(cat.form)
                cat.status=f"Added album {ar.name} to catalog."
            except Exception as e:
                cat.status=f"Failed to create album: {str(e)}"
                
        return str(cat)

    @app.route("/manna/albums/<album>")
    @flask_login.login_required
    def series_page(album):
        alb = vimongo.AlbumRecord.named(album)
        return str(pages.Album(alb))

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
