import flask, pages, vidstore
from urllib.parse import unquote
from datetime import datetime, timezone
from flask import url_for, request, Markup, render_template
from werkzeug.exceptions import HTTPException
from players import VideoPlayer
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap
from login import UserLoginManager

class Manna(flask.Flask):

    def __init__(self):
        super().__init__(__name__)
        self.config.from_pyfile("manna.cfg")
        csrf = CSRFProtect(self)
        mstore = vidstore.MannaStore(self.config)
        ulm = UserLoginManager(self)
        Bootstrap(self)

        @self.route("/")
        def index():
            return flask.redirect(url_for('.recents'))

        @self.route("/recent")
        def recents():
            pg = pages.RecentVideosPage(mstore, **request.args)
            if pg.is_playable:
                return render_player_for(pg)
            else:
                return flask.render_template("recents.html", page=pg)

        @self.route("/recent/edit/")
        @ulm.roles_required('Admin')
        def edit_recents():
            pg = pages.EditRecentVideosPage(mstore, **request.args)
            if pg.is_playable:
                return render_player_for(pg)
            if 'make_recent' in request.args:
                return pg.include_as_recent(request.args.get('make_recent'))
            return flask.render_template("missing_recent_vids.html", page=pg)

        @self.route("/archives")
        def view_archives():
            pg = pages.MannaStorePage(mstore, **request.args)
            if pg.has_json: 
                return pg.json
            else:
                return flask.render_template("catalog_page.html", page=pg)

        @self.route("/archives/<series>")
        @ulm.login_required
        def view_series(series):
            pg = pages.SeriesPage(mstore, series, **request.args)
            if pg.is_playable:
                return render_player_for(pg)
            elif pg.has_json:
                return pg.json
            else:
                return flask.render_template("series_page.html", page=pg)

        @self.route("/archives/<series>/edit", methods=['GET', 'POST', 'DELETE'])
        @ulm.roles_required('Admin')
        def edit_series_page(series):
            pg=pages.SeriesEditPage(mstore, series, **request.args)
            if pg.is_playable:
                return flask.redirect(url_for('.play_restricted', **request.args))
            elif pg.has_json:
                return pg.json
            else:
                return flask.render_template("series_edit_page.html", page=pg)


        @self.route("/archives/edit", methods=['GET', 'POST'])
        @ulm.roles_required('Admin')
        def edit_catalog_page():
            return pages.CatalogEditPage(mstore).response

        @self.route("/archives/<series>/videos/<video>/edit", methods=['GET', 'POST'])
        @ulm.roles_required('Admin')
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

        @self.route("/roku")
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

        @self.errorhandler(HTTPException)
        def error_page(err):
            mp = pages.MannaPage("Trouble in Paradise...")
            oe = getattr(err, 'original_exception', "")
            flask.flash(f"Error routing to {request.url} {err.description} {oe}")
            return flask.render_template("page.html", page=mp)

        def render_player_for(pg):
            if pg.has_audio:
                return flask.Response(pg.audio, mimetype="audio/mpeg")
            else:
                return flask.render_template("player.html", page=pg)

