import flask, flask_login, login, pages, config, mongo
from flask import Flask, url_for
from werkzeug.exceptions import HTTPException

class MannaFlask(flask.Flask):
    def make_response(self, rv):
        if isinstance(rv, pages.MannaPage):
            rv = rv.html
        return super().make_response(rv)

app = MannaFlask(__name__)
app.config.from_object(config)
latest_cnt = app.config.get("LATEST_CNT", 10)

mongo.init_flask(app)
login.init_flask(app)
pages.init_flask(app)

@app.route("/")
def list_latest():
    return pages.LatestVideosPage("Latest Lessons", mongo.Video.latest(latest_cnt))

@app.route("/latest/series/<series>/videos/<video>") 
def play_latest(series, video):
    video = mongo.video_for(series, video)
    if video in mongo.Video.latest(latest_cnt):
        return pages.VideoPage(video)
    else:
        return pages.ErrorPage(f"{video.name} is not a latest lesson")

@app.route("/series")
def show_catalog_page():
    mb = mongo.VideoSeries.objects()
    return pages.CatalogPage(mb)

@app.route("/series/edit", methods=['GET', 'POST'])
@login.required
def edit_catalog_page():
    return pages.CatalogEditPage(mongo.VideoSeries)

@app.route("/series/<series>")
@login.required
def show_series_page(series):
    return pages.SeriesPage(mongo.VideoSeries.named(series))

@app.route("/series/<series>/edit", methods=['GET', 'POST', 'DELETE'])
@login.required
def edit_series_page(series):
    return pages.SeriesEditPage(mongo.VideoSeries.named(series))

@app.route("/series/<series>/videos/<video>") 
@login.required
def play_restricted(series, video):
    return pages.VideoPage(mongo.video_for(series, video))

@app.route("/series/<series>/videos/<video>/edit", methods=['GET', 'POST'])
@login.required
def edit_video(series, video):
    return pages.VideoEditPage(mongo.video_for(series, video))

@app.route("/series/<series>/audios/<video>") 
def play_audio(series, video):
    return pages.AudioPage(mongo.video_for(series, video))

@app.route("/roku")
def roku():
    return pages.SeriesPage(mongo.Video.latest(10)).roku

@app.errorhandler(HTTPException)
def error_page(err):
    return pages.ErrorPage(err.description)

if __name__ == "__main__":
    app.run(ssl_context='adhoc', host="0.0.0.0", port=8001)
    #app.run(host="0.0.0.0", port=8001)
