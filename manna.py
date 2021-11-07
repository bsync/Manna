import config, pages, forms
from flask import Flask, redirect, url_for, request, jsonify
from werkzeug.exceptions import HTTPException
from vidstore import MannaStore
from tables import VideoTable, CatalogTable
from players import VideoPlayer
from flask_wtf.csrf import CSRFProtect
from login import LoginManager

class Manna(Flask):
    def __init__(self, cfg):
        super().__init__(__name__)
        self.config.from_object(cfg)
        csrf = CSRFProtect(self)
        lm = LoginManager(self)
        mstore = MannaStore()

        @self.route("/")
        def list_latest():
            vids = mstore.latest_videos(app.config['LATEST_CNT'])
            for vid in vids:
                vid.uri = url_for(".play_latest",
                                  series=vid.parent_series_name, 
                                  video=vid.name)
            mp = pages.MannaPage("Browse Latest")
            return mp.add(VideoTable(vids)).response

        @self.route("/latest/series/<series>/videos/<video>") 
        def play_latest(series, video):
            series = mstore.series_by_name(series)
            video = series.video_by_name(video)
            mp = pages.MannaPage("Play Latest")
            latest_vids = mstore.latest_videos(app.config['LATEST_CNT'])
            if video.uri in [ lv.uri for lv in latest_vids ]:
                mp.add(VideoPlayer(video))
            else:
                mp.show_errors(f"{video.name} is not recent")
            return mp.response

        @self.route("/catalog")
        def show_catalog_page():
            mp = pages.MannaPage("Browse Catalog")
            mp.add(CatalogTable(mstore.catalog, pageLength=25))
            return mp.response

        @self.route("/catalog/edit", methods=['GET', 'POST'])
        @lm.required
        def edit_catalog_page():
            mp = pages.MannaPage("Edit Catalog")
            mp.add(forms.AddSeriesToCatalogForm("Add Series"))
            mp.add(forms.SyncWithCatalogForm("Sync Catalog"))
            mp.add(CatalogTable(mstore.catalog, pageLength=10))
            return mp.response

        @self.route("/catalog/<series>")
        @lm.required
        def show_series_page(series):
            mp = pages.MannaPage(url_for('show_series_page', series=series))
            series = mstore.series_by_name(series)
            ra = request.args.copy()
            if ra.get('json', False): #This is an ajax request so respond with json
                ocolidx = int(ra['order[0][column]']) #table's current column sort idx
                ra['sort'] = ['last_user_action_event_date', 'alphabetical', 'alphabetical', 'duration'][ocolidx]
                ra['direction'] = ra['order[0][dir]']
                vids = series.videos(**ra)
                dtjson = jsonify(
                    dict(data=[[vid.date.strftime("%Y-%m-%d"), 
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

        @self.route("/catalog/<series>/edit", methods=['GET', 'POST', 'DELETE'])
        @lm.roles_required('Admin')
        def edit_series_page(series):
            series = mstore.series_by_name(series)
            mp = pages.MannaPage(url_for('show_series_page', series=series.name))
            mp.add(forms.AddVideoSetForm(series))
            mp.add(forms.PurgeVideoFromSeries(series))
            mp.add(forms.RedateSeriesForm(series))
            mp.add(forms.NormalizeSeries(series))
            mp.add(forms.SyncWithSeriesForm(series))
            return mp.response

        @self.route("/catalog/<series>/edit/move", methods=['POST'])
        @lm.roles_required('Admin')
        def move_video_to(series):
            series = mstore.series_by_name(series)
            avsf = forms.AddVideoSetForm(series)
            flask.flash(f"Added {avsf.vidnames} to {series.name}") 
            tc = [ f"{vname}:{vid}," for vname, vid in zip(avsf.vidnames, avsf.vidids) ]
            return redirect(url_for("edit_series_page", series=series.name, tcode=tc))

        @self.route("/catalog/<series>/videos/<video>") 
        @lm.required
        def play_restricted(series, video):
            series = mstore.series_by_name(series)
            video = series.video_by_name(video)
            turl = url_for('show_series_page', series=series.name)
            mp = pages.MannaPage(flask.Markup(f'{video.name} of <a href="{turl}">{series.name}</a>'))
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
            return pages.AudioPage(mongo.video_for(series, video))

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

app=Manna(config.DevelopmentConfig())
