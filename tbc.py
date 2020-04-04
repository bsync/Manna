import flask
import manna

app = flask.Flask(__name__)
app.config.from_object("config")
app.config['title']="Tullahoma Bible Church"
app.register_blueprint(manna.bp)
