import flask, flask_login
import pages, vimeo
from urllib.parse import unquote
from dotenv import load_dotenv 
try:
    import passcheck
    passcheck("fail early", "if it passcheck doesn't work")
except Exception as e:
    passcheck = lambda t,p : unquote(t).endswith(p)

load_dotenv()

def create_app(config=None):
    app = flask.Flask(__name__, static_url_path="/manna/static")
    app.config.from_object("config")
    print(f"FLask running in {app.env} mode!")
    vimeo.mdb.init_app(app)
    lm = flask_login.LoginManager(app)
    lm.login_view = 'login'

    class PageUser(flask_login.UserMixin): 
        def get_id(self): 
            return 0

    @lm.user_loader
    def load_user(user_id):
        rp = flask.request.path
        if flask.session.get(rp):
            return PageUser()
        else:
            return None

    @app.route('/manna/login', methods=['GET', 'POST'])
    def login():
        lp = pages.LoginPage(flask.request.args.get('next'))
        if lp.hasValidSubmission:
            if passcheck(lp.target, lp.guess):
                flask_login.login_user(PageUser())
                flask.session[lp.target]=True
                return flask.redirect(lp.target)
            else:
                return lp.render()
        else:
            return lp.render()

    @app.route("/manna/")
    def root():
        return pages.LatestLessons(10).render()

    @app.route("/manna/albums")
    def album_catalog():
        return pages.Catalog().render()

    @app.route("/manna/albums/<album>")
    @flask_login.login_required
    def album_page(album):
        return pages.Album(album).render()

    @app.route("/manna/albums/<album>/videos/<video>") 
    #@flask_login.login_required
    def video_page(album, video):
        return pages.VideoPlayer(album, video).render()

    return app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
