import flask, login, pages, config, mongo
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = flask.Flask(__name__)
app.config.from_object(config)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, { '/manna':app })
mongo.init_flask(app)
# Flask init the login manager and page manager
lm = login.init_flask(app)
pm = pages.init_flask(app)

@app.route('/auth', methods=['GET', 'POST'])
@lm.login_page
def auth():
    pg = pm.MannaPage(f"Authorization Required...")
    target = flask.request.args.get('next')
    return pg.authenticate(target)

@app.route("/")
def latest():
    pg = pm.MannaPage(f"Latest 10 Lessons")
    return pg.video_table(mongo.Video.latest(10), order=[[0,"desc"]])

@app.route("/roku")
def roku():
    pg = pm.MannaPage(f"Roku Lessons")
    return pg.roku_feed(mongo.Video.latest(10))

@app.route("/roku2")
def roku2():
    pg = pm.MannaPage(f"Roku Lessons")
    return pg.roku_feed(mongo.Video.latest(10))

@app.route("/latest/series/<series>/videos/<video>") 
def latest_player(series, video):
    pg = pm.MannaPage(f"{video} of {series}")
    video = mongo.video_for(series, video)
    return pg.play_video(video)
    #return video_player(series, video)

@app.route("/series/<series>/videos/<video>") 
@lm.login_required
def video_player(series, video):
    pg = pm.MannaPage(f"{video} of {series}")
    video = mongo.video_for(series, video)
    return pg.play_video(video)

@app.route("/series")
def show_catalog_page():
    pg = pm.MannaPage("Series Catalog")
    return pg.show_catalog(mongo.VideoSeries.objects()) 

@app.route("/edit/series", methods=['GET', 'POST'])
@lm.login_required
def edit_catalog_page():
    pg = pm.MannaPage("Series Catalog Editor")
    return pg.edit_catalog(mongo.VideoSeries)

@app.route("/series/<series>")
@lm.login_required
def show_series_page(series):
    pg = pm.MannaPage(f"Series {series}")
    series = mongo.VideoSeries.named(series)
    return pg.show_series(series)

@app.route("/edit/series/<series>", methods=['GET', 'POST', 'DELETE'])
@lm.login_required
def edit_series_page(series):
    pg = pm.MannaPage("Series Editor")
    series = mongo.VideoSeries.named(series)
    return pg.edit_series(series)

@app.route("/edit/series/<series>/videos/<video>", methods=['GET', 'POST'])
@lm.login_required
def edit_video(series, video):
    pg = pm.MannaPage("Video Editor")
    video = mongo.video_for(series, video)
    return pg.edit_video(video)

@app.route("/series/<series>/audios/<video>") 
def play_audio(series, video):
    pg = pm.MannaPage(f"Audio for Lesson {video} of series {series}")
    video = mongo.video_for(series, video)
    return pg.play_audio(video)

@app.route("/edit/reset")
@lm.login_required
def reset():
    import mongo
    import pdb; pdb.set_trace()
    mongo.init_db()
    return flask.redirect(flask.url_for('.latest'))

@app.errorhandler(HTTPException)
def error_page(err):
    pg = pm.MannaPage("Trouble in Paradise...")
    return pg.report_error(err)

