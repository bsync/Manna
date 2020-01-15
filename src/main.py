import flask
import flask_login
import flask_mongoengine 
import pages
from pages import tags as ptag
from pages import raw as praw
from urllib.parse import quote, unquote
from werkzeug.debug import DebuggedApplication

app = flask.Flask(__name__)
app.config.from_object("config")
if app.debug:
   print("FLask running in debug mode!")
   app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)
else:
   print("Flask running in production mode!")

db = flask_mongoengine.MongoEngine(app)
lm = flask_login.LoginManager(app)
lm.login_view = '/login'

class PageUser(flask_login.UserMixin): 
    def __init__(self, page):
        self.page = page

    def knowsPassword(self, guess):
        if unquote(self.page).endswith(guess):
            flask.session[self.page]=True
        return self.page in flask.session

    def get_id(self): 
        return 0

@lm.user_loader
def load_user(user_id):
    rp = flask.request.path
    if flask.session.get(rp):
        return PageUser(rp)
    else:
        return None

import vimeo, forms

@app.route("/")
def root():
    if app.debug: import pdb; pdb.set_trace() 
    page = pages.Page("Lessons", datatable="latest_table")
    with page.body:
        ptag.attr(style="background-color:black; color:blue;")
        ptag.h1("Pleroma Bible Church", style="text-align:center;")
        ptag.h2("Latest Lessons", style="text-align:center;color:gold")
        try: #to query vimeo for latest lessons
            with ptag.table(id="latest_table"):
                with ptag.thead(style="color: yellow;"):
                    ptag.th("Date", _class="dt-head-left")
                    ptag.th("Name", _class="dt-head-left")
                    ptag.th("Album", _class="dt-head-left")
                    ptag.th("Duration", _class="dt-head-left")
                with ptag.tbody():
                    for x in vimeo.VideoRecord.latest(10):
                        with ptag.tr():
                            ptag.attr(style="background-color:black;")
                            ptag.td(str(x.create_date), style="color:gold;")
                            ptag.td(ptag.a(x.name, href=quote(f"/albums/{x.album.name}/videos/{x.name}")))
                            ptag.td(ptag.a(x.album.name, href=quote(f"/albums/{x.album.name}")))
                            ptag.td(f"{int(x.duration/60)} mins", style="color:gold;")
        except Exception as err:
            ptag.div(ptag.h3("No Connection to Vimeo at the moment, check back later...", 
                                    style="text-align:center; color:red"))

    return page.render()

@app.route("/albums/<album>/videos/<video>")
def video_page(album, video):
    vid = vimeo.AlbumRecord.named(album).videoNamed(video)
    page = pages.Page(f"Lesson {vid.name} of {vid.album.name}")
    with page.body:
        ptag.attr(style="background-color:black; color:blue; text-align: center;")
        ptag.h1("Pleroma Bible Church"),
        ptag.h2(f"{vid.name} of {vid.album.name}"),
        ptag.div(praw(vid.html), style="display: flex; justify-content: center;")
        ptag.h3(ptag.a("Back to the Front", href="/"))
    return page.render()

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    form = forms.PasswordForm()
    pUser = PageUser(flask.request.args.get('next'))
    if form.validate_on_submit():
        if pUser.knowsPassword(form.data['guessword']):
            flask_login.login_user(pUser)
            return flask.redirect(pUser.page)
        else:
            error = f"Login with '{form.data['guessword']}' failed for '{pUser.page}'"
    page = pages.Page("Password")
    with page.body:
        ptag.attr(style="background-color:black; color:white; text-align: left;")
        ptag.h1("Pleroma Bible Church")
        ptag.h2(f"Provide password to access '{unquote(pUser.page)}'")
        with ptag.form(method="POST"):
            praw(str(form.hidden_tag()))
            praw(f"{form.guessword.label} : {form.guessword(size=10)}")
            praw(str(form.submit()))
            ptag.br()
            if error: ptag.p(f"{error}")
            ptag.br()
            ptag.a("Back to the Front", href="/")

    return page.render()

@app.route("/albums/<album>")
@flask_login.login_required
def album_page(album):
    alb = vimeo.AlbumRecord.named(album)
    page = pages.Page(f"Lessons of {alb.name}")
    with page.body:
        ptag.attr(style="background-color:black; color:blue; text-align: center;")
        ptag.h1("Pleroma Bible Church")
        ptag.h2(f"{alb.name}")
        praw(alb.html)# style="display: flex; justify-content: center;")
        ptag.h3(ptag.a("Back to the Front", href="/"))
    return page.render()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
