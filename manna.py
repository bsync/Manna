import flask, flask_login
import traceback
from flask import Flask, redirect, url_for, request, jsonify
from werkzeug.exceptions import HTTPException
from vidstore import MannaStore
from pages import Pages
from tables import VideoTable, CatalogTable
from players import VideoPlayer
try:
    import passcheck
except:
    passcheck = False

def create_app():
    app = Flask(__name__)

    if app.config["ENV"] == "production":
        app.config.from_object("config.ProductionConfig")
    else:
        app.config.from_object("config.DevelopmentConfig")

    mstore = MannaStore(app)
    pages  = Pages(app, mstore)
    forms = pages.forms

    @forms.login.register_view
    def do_login():
        if flask_login.current_user.is_authenticated:
            return redirect(url_for("list_latest"))
        mp = pages.MannaPage("Authorization Required...")
        target =  request.args.get('next', "")
        if passcheck and passcheck.handles(target):
            mp.add(forms.login.LoginForm(target))
        else:
            mp.add(forms.login.googleLoginForm(target))
        return mp.response

    @app.route("/")
    def list_latest():
        vids = mstore.latest_videos(app.config['LATEST_CNT'])
        for vid in vids:
            vid.uri = url_for(".play_latest",
                              series=vid.parent_series_name, 
                              video=vid.name)
        mp = pages.MannaPage("Latest Lessons")
        return mp.add(VideoTable(vids)).response

    @app.route("/latest/series/<series>/videos/<video>") 
    def play_latest(series, video):
        series = mstore.series_by_name(series)
        video = series.video_by_name(video)
        mp = pages.MannaPage("Play Latest Lesson")
        latest_vids = mstore.latest_videos(app.config['LATEST_CNT'])
        if video.uri in [ lv.uri for lv in latest_vids ]:
            mp.add(VideoPlayer(video))
        else:
            mp.show_errors(f"{video.name} is not a latest lesson")
        return mp.response

    @app.route("/catalog")
    def show_catalog_page():
        mp = pages.MannaPage("Catalog Listing")
        mp.add(CatalogTable(mstore.catalog, pageLength=25))
        return mp.response

    @app.route("/catalog/edit", methods=['GET', 'POST'])
    @forms.login.required
    def edit_catalog_page():
        mp = pages.MannaPage("Edit Catalog")
        mp.add(forms.AddSeriesToCatalogForm("Add Series"))
        mp.add(forms.SyncWithCatalogForm("Sync Catalog"))
        mp.add(CatalogTable(mstore.catalog, pageLength=10))
        return mp.response

    @app.route("/catalog/<series>")
    @forms.login.required
    def show_series_page(series):
        mp = pages.MannaPage(f"{series} Series")
        series = mstore.series_by_name(series)
        ra = request.args.copy()
        if ra.get('json', False): #This is an ajax request so respond with json
            ocolidx = int(ra['order[0][column]']) #table's current column sort idx
            ra['sort'] = ['date', 'alphabetical', 'alphabetical', 'duration'][ocolidx]
            ra['direction'] = ra['order[0][dir]']
            vids = series.videos(**ra)
            dtjson = jsonify(
                dict(data=[[ vid.date.strftime("%Y-%m-%d"), 
                            vid.parent_series_name, 
                            f"<a href={url_for('.play_restricted', series=series.name, video=vid.name)}>{vid.name}</a>", 
                            vid.duration ] for vid in vids],
                    draw=int(ra['draw']), 
                    recordsTotal=series.video_count, 
                    recordsFiltered=series.video_count))
            return dtjson
        else:
            ajsrc = url_for('show_series_page', series=series.name, json=True)
            mp.add(VideoTable(series.videos(length=10), ajax=f"'{ajsrc}'", serverSide="true"))
            return mp.response

    @app.route("/catalog/<series>/edit", methods=['GET', 'POST', 'DELETE'])
    @forms.login.required
    def edit_series_page(series):
        series = mstore.series_by_name(series)
        mp = pages.MannaPage(f"Edit {series.name} Series")
        mp.show_form(forms.AddVideoSetForm(series, 2))
        mp.show_form(forms.PurgeVideoFromSeries(series))
        mp.show_form(forms.RedateSeriesForm(series))
        mp.show_form(forms.NormalizeSeries(series))
        mp.show_form(forms.SyncWithSeriesForm(series))
        return mp.response

    @app.route("/catalog/<series>/videos/<video>") 
    @forms.login.required
    def play_restricted(series, video):
        series = mstore.series_by_name(series)
        video = series.video_by_name(video)
        mp = pages.MannaPage(f"{video.name} of {series.name}")
        mp.add(VideoPlayer(video))
        return mp.response

    @app.route("/catalog/<series>/videos/<video>/edit", methods=['GET', 'POST'])
    @forms.login.required
    def edit_video(series, video):
        mp = pages.MannaPage(f"Edit {series.name} Lesson {video}")
        series = mstore.series_by_name(series)
        video = series.video_by_name(video)
        redate=request.args.get('redate', False)
        #mp.playvid(video)
        if redate:
            video.redate(redate)
            return(f"Redated {video.name}: {redate}")
        if request.args.get('purge', False):
            video.purge()
            return(f"Purged {video.name}")
        return mp.response

    @app.route("/catalog/<series>/audios/<video>") 
    def play_audio(series, video):
        return pages.AudioPage(mongo.video_for(series, video))

    @app.route("/roku")
    def roku():
        mp = pages.MannaPage("Latest Lessons")
        vids = mstore.latest_videos(app.config['LATEST_CNT'])
        return mp.roku(vids)

    @app.errorhandler(HTTPException)
    def error_page(err):
        mp = pages.MannaPage("Routing Error:")
        oe = getattr(err, 'original_exception', "")
        mp.show_errors(f"Error routing to {request.url}", err.description, str(oe))
        return mp.response

    return app

if __name__ == "__main__":
    app = create_app()
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(ssl_context='adhoc', host="0.0.0.0", port=8001)
    #app.run(host="0.0.0.0", port=8001)
