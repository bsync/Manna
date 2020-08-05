import flask, flask_login, login, pages, config, mongo
from flask import Flask, redirect, url_for
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = flask.Flask(__name__)
app.config.from_object(config)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, { '/manna':app })

mongo.init_flask(app)
login.init_flask(app)
pages.init_flask(app)

@app.route("/")
def latest():
    pg = pages.MannaPage(f"Latest 10 Lessons")
    return pg.video_table(mongo.Video.latest(10), order=[[0,"desc"]])

@app.route("/latest/series/<series>/videos/<video>") 
def latest_player(series, video):
    pg = pages.MannaPage(f"{video} of {series}")
    video = mongo.video_for(series, video)
    return pg.play_video(video)

@app.route("/series/<series>/videos/<video>") 
@login.required
def video_player(series, video):
    pg = pages.MannaPage(f"{video} of {series}")
    video = mongo.video_for(series, video)
    return pg.play_video(video)

@app.route("/series")
def show_catalog_page():
    pg = pages.MannaPage("Series Catalog")
    return pg.show_catalog(mongo.VideoSeries.objects()) 

@app.route("/series/edit", methods=['GET', 'POST'])
@login.required
def edit_catalog_page():
    pg = pages.MannaPage("Series Catalog Editor")
    return pg.edit_catalog(mongo.VideoSeries)

#@login.required
@app.route("/series/<series>")
@flask_login.login_required
def show_series_page(series):
    pg = pages.MannaPage(f"Series {series}")
    series = mongo.VideoSeries.named(series)
    return pg.show_series(series)

@app.route("/series/<series>/edit", methods=['GET', 'POST', 'DELETE'])
@login.required
def edit_series_page(series):
    pg = pages.MannaPage("Series Editor")
    series = mongo.VideoSeries.named(series)
    return pg.edit_series(series)

@app.route("/series/<series>/videos/<video>/edit", methods=['GET', 'POST'])
@login.required
def edit_video(series, video):
    pg = pages.MannaPage("Video Editor")
    video = mongo.video_for(series, video)
    return pg.edit_video(video)

@app.route("/series/<series>/audios/<video>") 
def play_audio(series, video):
    pg = pages.MannaPage(f"Audio for Lesson {video} of series {series}")
    video = mongo.video_for(series, video)
    return pg.play_audio(video)

@app.route("/roku")
def roku():
    pg = pages.MannaPage(f"Roku Lessons")
    return pg.roku_feed(mongo.Video.latest(10))

@app.route("/reset/edit")
@login.required
def reset():
    import mongo
    import pdb; pdb.set_trace()
    mongo.init_db()
    return redirect(url_for('.latest'))

@app.errorhandler(HTTPException)
def error_page(err):
    pg = pages.MannaPage("Trouble in Paradise...")
    return pg.report_error(err)

if __name__ == "__main__":
    app.run(ssl_context='adhoc', host="0.0.0.0", port=8001)
