import config, pages, forms
from flask import Flask, redirect, url_for, request, flash, Markup, jsonify
from werkzeug.exceptions import HTTPException
from vidstore import MannaStore
from players import VideoPlayer
from flask_wtf.csrf import CSRFProtect
from login import UserLoginManager

class Manna(Flask):
    def __init__(self, cfg):
        super().__init__(__name__)
        self.config.from_object(cfg)
        csrf = CSRFProtect(self)
        lm = UserLoginManager(self)
        mstore = MannaStore()

        @self.route("/")
        def list_latest():
            vids = mstore.latest_videos(app.config['LATEST_CNT'])
            for vid in vids:
                vid.uri = url_for(".play_latest",
                                  series=vid.parent_name, 
                                  video=vid.name)
            return pages.VideoListPage("Latest Lessons", vids).response

        @self.route("/latest/series/<series>/videos/<video>") 
        def play_latest(series, video):
            series = mstore.series_by_name(series)
            video = series.video_by_name(video)
            latest_vids = mstore.latest_videos(app.config['LATEST_CNT'])
            if video.uri in [ lv.uri for lv in latest_vids ]:
                return pages.VideoPage("Play Latest", video).response
            else:
                return pages.ErrorPage(f"{video.name} is not recent").response

        @self.route("/catalog")
        def show_catalog_page():
            reqargs = self.ajax_url_for('show_catalog_page')
            return pages.CatalogPage(mstore, **reqargs).response

        @self.route("/catalog/edit", methods=['GET', 'POST'])
        @lm.roles_required('Admin')
        def edit_catalog_page():
            reqargs = self.ajax_url_for('show_catalog_page')
            return pages.CatalogEditPage(mstore, **reqargs).response

        @self.route("/catalog/<series>")
        @lm.required
        def show_series_page(series):
            series = mstore.series_by_name(series)
            reqargs = self.ajax_url_for('show_series_page', series=series.name)
            return pages.SeriesPage(series, **reqargs).response

        @self.route("/catalog/<series>/edit", methods=['GET', 'POST', 'DELETE'])
        @lm.roles_required('Admin')
        def edit_series_page(series):
            series = mstore.series_by_name(series)
            reqargs = self.ajax_url_for('show_series_page', series=series.name)
            return pages.SeriesEditPage(series, **reqargs).response

        @self.route("/catalog/<series>/edit/move", methods=['POST'])
        @lm.roles_required('Admin')
        def move_video_to(series):
            series = mstore.series_by_name(series)
            avsf = forms.AddVideoSetForm(series)
            flash(f"Added {avsf.vidnames} to {series.name}") 
            tc = [ f"{vname}:{vid}," for vname, vid in zip(avsf.vidnames, avsf.vidids) ]
            return redirect(url_for("edit_series_page", series=series.name, tcode=tc))

        @self.route("/catalog/<series>/videos/<video>") 
        @lm.required
        def play_restricted(series, video):
            series = mstore.series_by_name(series)
            video = series.video_by_name(video)
            turl = url_for('show_series_page', series=series.name)
            mp = pages.MannaPage(Markup(f'{video.name} of <a href="{turl}">{series.name}</a>'))
            mp.add(VideoPlayer(video))
            return mp.response

        @self.route("/catalog/<series>/videos/<video>/edit", methods=['GET', 'POST'])
        @lm.roles_required('Admin')
        def edit_video(series, video):
            mp = pages.MannaPage(f"Edit {series} {video}")
            series = mstore.series_by_name(series)
            video = series.video_by_name(video)
            redate=request.args.get('redate', False)
            #mp.playvid(video)
            if redate:
                video.redate(redate)
                return(f"Redated {video.name}: {redate}")
            if 'normalize' in request.args:
                vname = video.name
                video.save(name=series.normalized_name(vname))
                return(f"Normalized {vname} to {video.name}")
            if request.args.get('purge', False):
                video.purge()
                return(f"Purged {video.name}")
            return mp.response

        @self.route("/catalog/<series>/audios/<video>") 
        def play_audio(series, video):
            series = mstore.series_by_name(series)
            video = series.video_by_name(video)
            return pages.AudioPage(video).response

        @self.route("/roku")
        def roku():
            mp = pages.MannaPage("Latest Listing")
            vids = mstore.latest_videos(app.config['LATEST_CNT'])
            return mp.roku(vids)

        @self.errorhandler(HTTPException)
        def error_page(err):
            mp = pages.MannaPage("Routing Error:")
            oe = getattr(err, 'original_exception', "")
            mp.show_errors(f"Error routing to {request.url}", err.description, str(oe))
            return mp.response

    def ajax_url_for(self, endpoint, **uargs):
        reqargs = request.args.copy()
        reqargs.setdefault('ajax', url_for(endpoint, ajax='', **uargs))
        return reqargs
            


app=Manna(config.DevelopmentConfig())
