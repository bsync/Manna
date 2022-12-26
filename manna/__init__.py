import flask, time
from datetime import datetime, timezone
from flask import url_for, request, render_template
from flask_mail import Mail
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
from . import access, pages
from importlib import import_module
from urllib.parse import unquote

app = flask.Flask(__name__)
app.config.from_prefixed_env()
app.config.from_mapping({ "DEBUG": True, })

mmailer = Mail(app)
maccess = access.Mannager(app, mailer=mmailer) 
mpages = pages.Mannager(app)

#Import the configured storage module, defaulting to 'local'
mstoremod = import_module(f"manna.storage.{app.config.get('STORAGE_MANNAGER', 'local')}")
mstore = mstoremod.Mannager(app.config.get('STORE_MANNAGER_ROOT', '/catalog'))

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
    return flask.redirect(flask.url_for("show_recent"))

@app.route("/")
def index():
    return flask.redirect(url_for('show_recent'))

def render(template, **kwargs):
    return flask.render_template(
            template, 
            title=app.config.get('TITLE', 'Manna'),
            **kwargs)

@app.route("/recent/")
def show_recent(series=None, vid=None):
    if vid:
        series = mstore.series_by_name(series)
        vid = series.video_by_name(vid)
    recents = mstore.recent_videos(app.config.get('LATEST_CNT', 10))
    return render('recents.html', playvid=vid, videos=recents)

@app.route("/play/<series>")
def play(series):
    series = mstore.series_by_name(series)
    if "dt_json" in request.args:
        kwargs = request.args.copy()
        svids = series.videos(**kwargs) 
        qdicts = [ dict(id=id(x),
                   date=x.date.strftime("%Y-%m-%d"), 
                   name=x.name, 
                   duration=str(x.duration)) for x in svids ]
        return flask.jsonify(dict(
            data=qdicts,
            draw=int(kwargs['draw']), 
            recordsTotal=svids.available, 
            recordsFiltered=svids.available))
    elif 'video' in request.args:
        vid = series.video_by_name(request.args['video'])
        return render('series.html', series=series, playvid=vid)
    elif 'audio' in request.args:
        vid = series.video_by_name(request.args['audio'])
        return render('series.html', series=series, playvid=vid, playaudio=True)
        #return flask.Response(vid.audio_stream, mimetype="audio/mpeg")
    else:
        return render('series.html', series=series)

@app.route("/recent/edit/")
@maccess.login_required
@maccess.admin_required
def edit_recents():
    pg = mpages.EditRecentVideosPage(mstore, **request.args)
    if 'make_recent' in request.args:
        return pg.include_as_recent(request.args.get('make_recent'))
    return pg.response

@app.route("/archives") 
def view_archives():
    return render('catalog.html', catalog=mstore.series.values())

@app.route("/download/<series>")
def download(series):
    series = mstore.series_by_name(series)
    if 'video' in request.args:
        video = series.video_by_name(request.args['video'])
        vrp = unquote(str(video.relative_path))
        return flask.send_from_directory(mstore.rootdir, vrp, as_attachment=True)
    elif 'audio' in request.args:
        video = series.video_by_name(request.args['audio'])
        if not video.audio_file.exists():
            video.generate_audio_file()
        response = flask.make_response(video.audio_stream)
        response.headers.set(
            'Content-Disposition', 'attachment', filename=str(video.relative_stem.with_suffix('.mp3')))
        return response

@app.route("/play/<series>/edit", methods=['GET', 'POST', 'DELETE'])
@maccess.login_required
@maccess.admin_required
def edit_series_page(series):
    if "dt_json" in request.args:
        return flask.redirect(flask.url_for("play", series=series, **request.args))
    series = mstore.series_by_name(series)
    if 'upload' in request.args:
        upfile = request.files['file']
        if upfile.filename == '':
            return 'No file selected'
        safeUpfile = "".join(c for c in upfile.filename if c.isalnum() or c in " #.")
        upfile.save(series.path.joinpath(safeUpfile))
        return f"Finished upload for {safeUpfile}!"
    return render('editseries.html', series=series,
                    add_videos_form=forms.AddVideoSet(series),
                    purge_video_form=forms.PurgeVideo(series),
                    redate_series_form=forms.RedateSeries(series),
                    normalize_series_form=forms.NormalizeTitles(series))

@app.route("/archives/<series>/videos/<video>/edit", methods=['GET', 'POST'])
@maccess.login_required
@maccess.admin_required
def edit_video(series, video):
    try:
        series = mstore.series_by_name(series)
        if 'move_to' in request.args:
            import pdb; pdb.set_trace()
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

