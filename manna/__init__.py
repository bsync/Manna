import flask
from datetime import datetime, timezone
from flask import url_for, request, render_template
from werkzeug.exceptions import HTTPException
import access, pages, storage

app = flask.Flask(__name__)
app.config.from_prefixed_env()

maccess = access.Mannager(app) 
mpages = pages.Mannager(app)
mstore = storage.Mannager(app)

@app.route("/login", methods=['GET', 'POST'])
def login():
    pg = mpages.LoginPage(maccess)
    if pg.needs_redirection:
        return pg.redirection
    else:
        return flask.render_template("login_form.html", page=pg)

@app.route("/logout", methods=['GET'])
def logout():
    maccess.logout()
    return flask.redirect(flask.url_for("recents"))

@app.route("/")
def index():
    return flask.redirect(url_for('recents'))

@app.route("/recent")
def recents():
    pg = mpages.RecentVideosPage(mstore, **request.args)
    if pg.is_playable:
        return render_player_for(pg)
    else:
        return flask.render_template("recents.html", page=pg)

@app.route("/recent/edit/")
@maccess.admin_required
def edit_recents():
    pg = mpages.EditRecentVideosPage(mstore, **request.args)
    if pg.is_playable:
        return render_player_for(pg)
    if 'make_recent' in request.args:
        return pg.include_as_recent(request.args.get('make_recent'))
    return flask.render_template("missing_recent_vids.html", page=pg)

@app.route("/archives")
def view_archives():
        pg = mpages.CatalogStorePage(mstore, **request.args)
        if pg.has_json: 
            return pg.json
        else:
            return flask.render_template("catalog_page.html", page=pg)

@app.route("/archive/<series>")
def view_archive(series=None):
    pg = mpages.SeriesPage(mstore, series, **request.args)
    if pg.is_playable:
        return render_player_for(pg)
    elif pg.has_json:
        return pg.json
    else:
        return flask.render_template("series_page.html", page=pg)

@app.route("/archives/<series>/edit", methods=['GET', 'POST', 'DELETE'])
@maccess.admin_required
def edit_series_page(series):
    pg=mpages.SeriesEditPage(mstore, series, **request.args)
    if pg.is_playable:
        return flask.redirect(url_for('.play_restricted', **request.args))
    elif pg.has_json:
        return pg.json
    else:
        return flask.render_template("series_edit_page.html", page=pg)


@app.route("/archives/<series>/videos/<video>/edit", methods=['GET', 'POST'])
@maccess.admin_required
def edit_video(series, video):
    try:
        series = mstore.series_by_name(series)
        if 'move_to' in request.args:
            series.add_videos(request.args['move_to'])
            return(f"{video} moved to {series.name}")
        else:
            video = series.video_by_name(video)
            if 'redate' in request.args:
                newdate = request.args['redate']
                video.redate(newdate)
                mstore.adjust_recents(video)
                return(f"Redated {video.name} to {newdate}")
            if 'normalize' in request.args:
                vname = video.name
                video.save(name=series.normalized_name(vname))
                return(f"Normalized {vname} to {video.name}")
            if 'purge' in request.args:
                series.purge_video(video.name)
                return(f"Purged {video.name}")
            raise Exception("Not a valid edit operation for {video.name} of {series.name} !")
    except Exception as ex:
        return str(ex)

@app.route("/roku")
def roku():
    tstamp = datetime.now(tz=timezone.utc)
    tstamp = tstamp.isoformat(timespec="seconds")
    rfeed = dict(
        providerName="Pleroma Videos",
        lastUpdated=tstamp,
        language='en',
        movies=[dict(id=x.uri.split('/')[2],
                    title=f"{x.parent_name}-{x.name}",
                    genres=["faith"],
                    tags=["faith"],
                    thumbnail=x.plink,
                    content=dict(
                         dateAdded=x.date.strftime("%Y-%m-%d"),
                         duration=str(x.duration),
                         videos=[
                            dict(url=x.vlink, 
                                 quality="HD", 
                                 videoType="MP4"), ],),
                   releaseDate=tstamp,
                   shortDescription=x.parent_name,)
                for i,x in enumerate(mstore.recent_videos) ],)
    return flask.jsonify(rfeed)


@app.errorhandler(HTTPException)
def error_page(err):
    mp = mpages.MannaPage("Trouble in Paradise...")
    oe = getattr(err, 'original_exception', "")
    flask.flash(f"Error routing to {request.url} {err.description} {oe}")
    return flask.render_template("page.html", page=mp)

def render_player_for(pg):
    if pg.has_audio:
        return flask.Response(pg.audio, mimetype="audio/mpeg")
    else:
        return flask.render_template("player.html", page=pg)

