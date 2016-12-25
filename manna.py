import flask
from wtforms import Form, PasswordField, SelectField, SubmitField, validators
from flask_bootstrap import Bootstrap
from resources import Catalog, Scripture

app = flask.Flask(__name__)
app.secret_key = 'manna'
Bootstrap(app)
catalog = Catalog('lessons')

@app.route('/')
def renderCatalog():
    #flask.session.clear()
    return flask.render_template('catalog.jinja', catalog=catalog)

@app.route('/catalog/<sname>', methods=['GET', 'POST'])
def renderSeries(sname):
    class AuthForm(Form):
        password = PasswordField(u'Password', [validators.Length(min=4)])
    form = AuthForm(flask.request.form)
    if flask.request.method == 'POST' and form.validate():
	return flask.render_template('series.jinja', series=catalog.series(sname))
    return flask.render_template('login.html', form=form)

@app.route('/catalog/<sname>/<lname>')
def renderLesson(sname, lname):
    lseries = catalog.series(sname)
    lseries.selection = lseries.lesson(lname)
    return flask.render_template('series.jinja', series=lseries)

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
    bform = BibleForm(Scripture("static/KingJamesText"), flask.request.form)
    return flask.render_template('scripture.jinja', form=bform)

if __name__ == '__main__':
    app.run()
