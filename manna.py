import flask
import flask_login
from flask import request, Response, url_for
from wtforms import Form, PasswordField, SelectField, SubmitField
from flask_bootstrap import Bootstrap
from resources import Catalog, Scripture
from urllib.parse import urlparse, urljoin

#Setup Flask App framework
app = flask.Flask(__name__)
app.secret_key = 'manna'
Bootstrap(app)

#Setup the login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "thou_shalt_not_pass"

#Load catalog (using AWS S3 if possible)
cat = Catalog('lessonset', bucket_name="www.pleromabiblechurch.org")

@app.route('/')
def renderCatalog():
     flask_login.logout_user()
     return flask.render_template('catalog.jinja', catalog=cat)
     #return flask.jsonify([x.name for x in cat.xseries])

@app.route('/catalog/<sname>')
@flask_login.login_required
def renderSeries(sname):
     return flask.render_template('series.jinja', series=cat.series(sname))
     #return flask.jsonify(cat.series(sname))

@app.route('/catalog/<sname>/<lname>')
@flask_login.login_required
def renderLesson(sname, lname):
    ser = cat.series(sname)
    les = ser.lesson(lname)
    if request.args.get('astype')  == 'mp3':
        resp = flask.make_response(flask.redirect(les.mp3.url))
        resp.set_cookie('fileDownloadToken', les.name);
        return resp

    return flask.render_template('series.jinja', series=ser, selection=les)
    #return flask.jsonify(cat.series(sname).lesson(lname))

@app.route('/upload')
@app.route('/upload/<ser>', methods=['GET', 'POST'])
@flask_login.login_required
def upload(ser=None):
    if request.method == 'POST' and request.files:
    # check if the post request has the file part
        if not request.files:
            flask.flash('No file part')
            return flask.redirect(request.url)
        files = request.files.getlist("file[]")
        # if user does not select file, browser also
        # submit a empty part without filename
        for f in files:
            if f.filename == '':
                flask.flash('No selected file')
                return flask.redirect(request.url)
            cat.series(ser).addLesson(f.filename)
    return flask.render_template('upload.jinja', catalog=cat, series=ser)

@app.route('/scripture/', methods=['GET', 'POST'])
def renderScripture():
     class BibleForm(Form):
          bookSel = SelectField(u'Book', default='Genesis')
          chapSel = SelectField(u'Chapter', default='chapt 1')
          verseSel = SelectField(u'Verse', default='verse 1')
          submission = SubmitField()
          def __init__(self, bible, fdata):
                Form.__init__(self, fdata)
                self.bookSel.choices = [ self.pair(x.name) for x in bible.canon ]
                book = bible.book(self.bookSel.data) #Convert name to actual book
                chpt = book.chapter(int(self.chapSel.data.split()[-1]))
                self.chapSel.choices = [ self.cpair(x) for x in range(1, len(book)+1) ]
                self.verseSel.choices = [ self.vpair(x) for x in range(1, len(chpt.verses)) ]
                self.verses = chpt.verses
          def pair(self, x):  return (x,x)
          def cpair(self, x): return self.pair("chapt %s" % x)
          def vpair(self, x): return self.pair("verse %s" % x)
     bform = BibleForm(Scripture("static/KingJamesText"), request.form)
     return flask.render_template('scripture.jinja', form=bform)

users = {}
@login_manager.user_loader
def load_user(userid):
    return users.get(userid)

@app.route('/login', methods=["GET", "POST"])
def thou_shalt_not_pass():
    #Internal safe target check...
    def is_safe_url(target):
         ref_url = urlparse(request.host_url)
         test_url = urlparse(urljoin(request.host_url, target))
         return test_url.scheme in ('http', 'https') and \
                  ref_url.netloc == test_url.netloc

    #Internal login form representation
    if request.method == 'POST':
        next = request.args.get('next')
        if not is_safe_url(next):
            return flask.abort(400)
        if cat.checkPassForUrl(request.form['password'], next):
            class User(flask_login.UserMixin):
              def __init__(self, uid):
                  self._id = uid
              def get_id(self):
                  return self._id
            newUser = User(len(users))
            users[newUser.get_id()]=newUser
            flask_login.login_user(newUser)
            flask.flash('Logged in successfully.')
            return flask.redirect(next or flask.url_for('index'))
        else:
            return flask.render_template('catalog.jinja', catalog=cat, dologin="Try Again!")
    else:
        return flask.render_template('catalog.jinja', catalog=cat, dologin="")


if __name__ == '__main__':
     app.run(threaded=True)
