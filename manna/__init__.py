import flask
from datetime import datetime, timezone
from flask import url_for, request, render_template
from flask_mail import Mail
from werkzeug.exceptions import HTTPException
from . import access, pages, storage
from flask_caching import Cache

app = flask.Flask(__name__)
app.config.from_prefixed_env()
app.config.from_mapping({ 
    "DEBUG": True, 
    "CACHE_TYPE": "FileSystemCache",  
    "CACHE_DIR": "/tmp",
    "CACHE_DEFAULT_TIMEOUT": 300 })

cache = Cache(app)
mmailer = Mail(app)
maccess = access.Mannager(app, mailer=mmailer) 
mpages = pages.Mannager(app)
mstore = storage.Mannager(app)

@app.route("/login", methods=['GET', 'POST'])
def login():
    pg = mpages.LoginPage(maccess)
    if pg.login_form_was_submitted:
        return maccess.login_via_email(pg.email, pg.password)
    elif pg.request_form_was_submitted:
        return maccess.request_access(pg.email, pg.comments)
    elif pg.google_login_form_was_submitted: 
        return maccess.login_via_google()
    elif pg.invite_access_form_was_submitted: 
        return maccess.invite_access(pg.email, pg.comments)
    else:
        return flask.render_template("login_form.html", page=pg)

@app.route("/register", methods=['GET', 'POST'])
@maccess.login_required
@maccess.admin_required
def register():
    pg = mpages.RegistrationPage(maccess)
    if pg.register_user_form_was_submitted:
        return maccess.register(pg.selected_user)
    else:
        return flask.render_template("regform.html", page=pg)

@app.route("/logout", methods=['GET'])
def logout():
    maccess.logout()
    return flask.redirect(flask.url_for("recents"))

@app.route("/")
def index():
    return flask.redirect(url_for('recents'))

@app.route("/recent")
def recents():
    return mpages.RecentVideosPage(mstore, **request.args).response

@app.route("/recent/edit/")
@maccess.login_required
@maccess.admin_required
def edit_recents():
    pg = mpages.EditRecentVideosPage(mstore, **request.args)
    if 'make_recent' in request.args:
        return pg.include_as_recent(request.args.get('make_recent'))
    return pg.response

@app.route("/archives") 
@cache.memoize()
def view_archives():
    return mpages.CatalogStorePage(mstore, **request.args).response

@app.route("/catalog/edit/")
def edit_archives():
    cache.delete_memoized(view_archives)
    return mpages.CatalogEditPage(mstore, **request.args).response

@app.route("/archives/<series>")
def view_archive(series):
    return mpages.SeriesPage(mstore, series, **request.args).response

@app.route("/archives/<series>/edit", methods=['GET', 'POST', 'DELETE'])
@maccess.login_required
@maccess.admin_required
def edit_series_page(series):
    return mpages.SeriesEditPage(mstore, series, **request.args).response

@app.route("/archives/<series>/videos/<video>/edit", methods=['GET', 'POST'])
@maccess.login_required
@maccess.admin_required
def edit_video(series, video):
    try:
        series = mstore.series_by_name(series)
        if 'move_to' in request.args:
            series.add_videos(request.args['move_to'])
            cache.delete_memoized(view_archive, series.name)
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
                nvname = series.normalized_name(vname)
                video.save(name=nvname)
                return(f"Normalized {vname} to {nvname}")
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
                         duration=x.duration.seconds,
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

