import flask, os, traceback, bcrypt
import wtforms.fields as fields
import wtforms.validators as validators
from wtforms.fields.html5 import DateField, EmailField
from datetime import datetime, date
from flask_wtf import FlaskForm
from tables import VideoTable, UserTable
from vidstore import MannaStore
from models import mdb, User, Role


class Submital(str):
    def __new__(cls, content, **kwargs):
        return str.__new__(cls, content)

    def __init__(self, istr, disabled=False):
        super().__init__()
        self.istr = istr
        self.booleans = "disabled" if disabled else ""

    @property
    def id(self):
        return self.istr


class MannaForm(FlaskForm):
    submital = Submital("Manna_Form")
    form_id = fields.HiddenField("form_id") 
    vimeo_token_field = fields.HiddenField(default=os.getenv('VIMEO_TOKEN'))
    scripts = [ "https://code.jquery.com/jquery-3.6.0.min.js"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mstore = MannaStore()
        self.today=f"{date.today().isoformat()}"
        self.template_vars = dict(form=self)
        if self.was_submitted:
            try:
                self.on_validated()
            except Exception as e:
                emsg = str(e) + traceback.format_exc()
                flask.flash(f"Operation failed for {self}: {emsg}")

    @property
    def name(self):
        return self.submitals[0]

    @property
    def submitals(self):
        return [ self.submital ]

    @property
    def was_submitted(self):
        return self.validate_on_submit() and flask.request.form['form_id'] == self.name

    def on_validated(self):
        pass

    def __getattr__(self, name):
        if name in flask.request.form:
            return flask.request.form['name']
        else:
            raise AttributeError(f"{name} not found in {self}")


class AddSeriesToCatalogForm(MannaForm):
    submital = Submital("Add_a_series_to_the_catalog")
    series_name = fields.StringField("Name the Series", [validators.InputRequired()])

    def on_validated(self):    
        aseries = self.mstore.add_new_series(self.series_name.data, "TODO: Describe me")
        self.redirect(with_msg=f"Added series {aseries.name}")


class SyncWithCatalogForm(MannaForm):
    submital = Submital("Sync_entire_catalog_with_backing_store")

    def on_validated(self):    
        self.mstore.clear_cache()
        self.redirect(with_msg=f"Cached series have been refreshed...")


class SeriesForm(MannaForm):
    submital = Submital("Series_Form")
    table_options = { 'pageLength':5 }

    def __init__(self, series, *args, **kwargs):
        self.series = series
        super().__init__(*args, **kwargs)
        tbopts = dict(pageLength=5)
        tbopts.update(self.table_options)
        self.table = VideoTable(self.videos, **tbopts)
        self.template_vars.update(self.table.template_vars)
        self.scripts.extend(self.table.scripts)
        self.css = self.table.css
    
    @property
    def scriptage(self):
        return self.table.scriptage

    @property
    def videos(self):
        return self.series.videos()


class AddVideoForm(SeriesForm):
    submital = Submital("Add_Video")
    video_name = fields.StringField("Video Name:", [validators.InputRequired()])
    video_author = fields.StringField("Presented by:", [validators.InputRequired()])
    video_file = fields.FileField("Video File:", [validators.InputRequired()])
    video_date = DateField("Video Date:", [validators.InputRequired()], default=date.today())
    series_id = fields.HiddenField("series id")
    series_uri = fields.HiddenField("series uri")
    vid_id = fields.HiddenField("uploaded video ids")


class AddVideoSetForm(SeriesForm):
    template = "add_video_set.html"
    submital = Submital("Upload_Videos")

    def __init__(self, series, cnt=2, *args, **kwargs):
        super().__init__(series, *args, **kwargs)
        self.vimeo_token = os.getenv('VIMEO_TOKEN')
        self.vidups = []
        for vidx in range(0,cnt):
            self.vidups.append(
                AddVideoForm(series, 
                             *args, 
                             video_name=series.nth_next_vidname(vidx+1)))
        self.scripts.extend([ 
            "https://code.jquery.com/jquery-3.6.0.min.js", 
            "vimeo-upload.js", ]) 

    def on_validated(self):    
        self.vidids = [ vid for vid in flask.request.form.getlist('vid_id') if vid ]
        self.vidnames = flask.request.form.getlist('video_name')[:len(self.vidids)]
        flask.flash(f"Added {self.vidnames} to {self.series.name}") 
        self.mstore.purge_cache(self.series)

    @property
    def scriptage(self):
        return """
            $(".upunit:not(:first)").hide()
            $(".del_field").hide()
            $(".add_field").click(function(e) {
                e.preventDefault()
                if ($(".upunit:hidden").length > 0) {
                        $(".upunit:hidden:first").show()
                } 
                if ($(".upunit:hidden").length == 0) {
                        $(".add_field").hide()
                        $(".del_field").show()
                }
            })
            $(".del_field").click(function(e) {
                e.preventDefault()
                if ($(".upunit:visible").length > 0) {
                        $(".upunit").last().hide()
                } 
                if ($(".upunit:visible").length == 1) {
                        $(".add_field").show()
                        $(".del_field").hide()
                }
            }) 

            $("#Upload_Videos_submit").click(function(evt) {
               evt.stopPropagation()
               evt.preventDefault()
               var ups = $.map($(".upunit:visible"), function(unit) { return perform_upload_for(unit) })
               //$.when(...ups).done(function() { $("#Upload_Videos").submit() })
            })

            function perform_upload_for(unit) {
               var upfile = $(unit).children(".video_file")[0].files[0]
               var vidname = $(unit).children(".video_name").val()
               var progbar = $(unit).children(".progress")[0]
               var results = $(unit).children(".status")
               var vidout = $(unit).children(".vid_id")
               var vimtoken = $("#vimeo_token_field").val()
               var seriesid = $(unit).children(".series_id").val()
               results.html("")

               function showMessage(html, type) {
                   results.attr('class', 'status alert alert-' + (type || 'success'))
                   results.html(html)
               }

               function move_to_series(vidid) { 
                    return new Promise( (resolve) => {
                        $.ajax({url: `https://api.vimeo.com/me/projects/${seriesid}/videos/${vidid}`,
                                type: "PUT",
                                beforeSend: function(xhr) { 
                                    xhr.setRequestHeader('Authorization', 'Bearer ' + vimtoken); }, 
                                success: function (resp) {
                                    showMessage(`Uploaded <strong>${vidname}</strong> ` +
                                                                    `to series ${seriesid}`)
                                    vidout.val(vidid) 
                                    resolve(vidid)
                                }, 
                                error: function (xhr, ts, ex) {
                                    showMessage(`Upload of <strong>${vidname}</strong> ` +
                                                `to series ${seriesid} failed with error: ${ts}`)
                                }, })
                    })
                }

                function wait_for_transcode(vidid) {
                    var tm=0, timer=setInterval(function(){tm++},1000);
                    showMessage(`Waiting for transcode to complete for: <strong>${vidname}</strong>`)
                    return new Promise( (resolve) => {
                        function poll_transcode_status() {
                            $.ajax({url: `https://api.vimeo.com/videos/${vidid}` 
                                         + "?fields=uri,upload.status,transcode.status",
                                    type: "GET",
                                    beforeSend: function(xhr) { 
                                        xhr.setRequestHeader('Authorization', 
                                                             'Bearer ' + vimtoken); }, 
                                    success: function (resp) {
                                        if (resp.transcode.status != "complete") {
                                            showMessage(`Transcode status after ${tm} seconds: ${vidname} ` 
                                                       +`<strong> ${resp.transcode.status} </strong>` )
                                            setTimeout(poll_transcode_status, 3000, vidid) 
                                        }
                                        else { 
                                            showMessage(`Transcode complete for: <strong> ${vidname} </strong>`)
                                            resolve(vidid)
                                        } } })
                        }
                        poll_transcode_status()
                    })
                }

               vup_promise = new Promise((resolve,reject) => {
                    vup = new VimeoUpload({
                         name: vidname,
                         description: "TODO",
                         private: false,
                         file: upfile,
                         token: vimtoken,
                         upgrade_to_1080: true,
                         onError: function(data) {
                            showMessage('<strong>Error</strong>: ' 
                                        + JSON.parse(data).error, 'danger') },
                         onProgress: function(data) {
                            updateProgress(data.loaded / data.total, progbar) },
                         onComplete: (vuri) => resolve(vuri),
                            })
                    vup.upload() })
                    return vup_promise.then(move_to_series).then(wait_for_transcode)
            }

            function updateProgress(progress, bar) {
                progress = Math.floor(progress * 100)
                $(bar).attr('style', 'background-color: blue; width:' + progress + '%')
                $(bar).html('&nbsp;' + progress + '%')
            }
            """


class PurgeVideoFromSeries(SeriesForm):
    template = "purge_video.html"
    submital = Submital("Purge_Video")
    vidlist = fields.SelectField("Choose a video to purge:", validate_choice=False) 
    table_options = { 'select':{ 'style':'single'} }

    def __init__(self, series, *args, **kwargs):
        super().__init__(series, *args, **kwargs)
        self.vidlist.choices = [ v.name for v in series.videos() ]

    def on_validated(self):    
        resp = self.series.purge_video(self.vidlist.data)
        if resp.status_code != 204:
            flask.flash(resp.text)
        else:
            flask.flash(f"Purged {self.vidlist.data}")

    @property
    def scriptage(self):
        return """$("#Purge_Video_submit").click(function(evt) {
                    return window.confirm(`Remove ${$('#vidlist').val()}?`)
                }) """


class RedateSeriesForm(SeriesForm):
    template = "redate_form.html"
    submital = Submital("Redate Videos")
    table_options = { 'select':{ 'style':'multi'} }
    start_date = fields.DateField(id="start_date") 
    date_inc = fields.IntegerField(id="date_inc", default=3, render_kw=dict(size=2))
    vid_set = fields.IntegerField(id="vid_set", default=2, render_kw=dict(size=2))

    def __init__(self, series, *args, **kwargs):
        super().__init__(series, *args, **kwargs)
        self.scripts.extend([ "date.format.js" ])

    @property
    def initial_date(self):
        return self.start_date(value=date.today().isoformat())

    @property
    def scriptage(self):
        return f"var dtable = {self.table.scriptage}\n" + \
                """ 
                var selected = [];
                $('#start_date').datepicker({dateFormat: "yy-mm-dd"})
                $('#vid_set').spinner({step: 1, min: 1, max: 3})
                $('#date_inc').spinner({step: 1, min: 1, max: 3})
                function set_redate_strategy(etype) {
                   if (etype === 'row') {
                        var srows = dtable.rows('.selected').data()
                        srows = srows.map(function(v) { return $(v[2]).text() })
                        if ( srows.length == 0) {
                            $('#strategy').text('Redate all items in the order listed ')
                        }
                        else if ( srows.length == 1 ) {
                            $('#strategy').text(`Redate items in the order listed from ${srows[0]} `)
                        }
                        else if ( srows.length == 2 ) {
                            $('#strategy').text(`Redate items in the order listed from ${srows[0]} up to ${srows[1]} `)
                        }
                        else { 
                            $('#strategy').text('Redate the selected items in the order listed')
                        }
                   }
                }
                set_redate_strategy('row')
                function changing_selection(e,dt,type,idxs) { set_redate_strategy(type) }
                dtable.on('select', changing_selection)
                dtable.on('deselect', changing_selection)
                $("#RedateVideos input[type=submit]").click(
                  function(evt) { 
                    evt.preventDefault()
                    var vc = dtable.rows('.selected').data()
                    if (vc.length == 0) { dtable.rows().select() }
                    else if (vc.length == 2) { 
                        ridxs = dtable.rows().indexes()
                        sidxs = dtable.rows('.selected')
                        sidxs = sidxs.indexes()
                        dtable.rows(
                            /* note: the row indices used by datatables are NOT the same 
                               as the order of the actual table's rows. Therefore we
                               must use indexOf to compare positions.*/
                            function (idx, data, node) { 
                                return ridxs.indexOf(idx) >= ridxs.indexOf(sidxs[0]) && 
                                       ridxs.indexOf(idx) <= ridxs.indexOf(sidxs[1])
                            }).select()
                    }
                    vc = dtable.rows('.selected').data()
                    var vm = vc.map(function(v) { return $(v[2]).text() })
                    var date = new Date($('#start_date').val() + "T00:00")
                    var dinc = parseInt($('#date_inc').val())
                    var vcnt = parseInt($('#vid_set').val())
                    for (let lname of vm.toArray()) {
                        dout = date.format('yyyy-mm-dd')
                        $.ajax({url: escape(`videos/${lname}/edit`)+`?redate=${dout}`, 
                                 async: false,
                                 success: function(result) { 
                                   $('#RedateVideos_form_results').html(result) } })
                        vcnt = vcnt - 1
                        if (vcnt == 0) {
                            vcnt = $('#vid_set').val()
                            date.setDate(date.getDate() + dinc)
                        }
                    }
                    window.location.reload()
                }) 

                """
    

class NormalizeSeries(SeriesForm):
    template = "normalize_form.html"
    submital = Submital("Normalize_Titles")

    def __init__(self, series, *args, **kwargs):
        super().__init__(series, *args, **kwargs)
        if not self.is_noramlizable:
            self.booleans = "disabled" 

    @property
    def videos(self):
        return self.series.normalizable_vids

    @property
    def is_noramlizable(self):
        return len(self.series.normalizable_vids) > 0

    @property
    def example(self):
        if self.is_noramlizable:
            evids = self.series.normalizable_vids
            evid = evids[0]
            e_norm_name = self.series.normalized_name(evid.name)
            return f"""There are a total of {len(evids)} videos to normalize. 
                       For example: {evid.name} would be normalized to {e_norm_name}"""
        else:
            return f"""Nothing to normalize in series "{self.series.name}" at this time.""" 

    def on_validated(self):    
        self.mstore.purge_cache(self.series)
        flask.flash(f"Normalized series {self.series.name}")

    @property
    def scriptage(self):
        return f"var ndtable = {self.table.scriptage}\n" + \
              """$("#Normalize_Titles input[type=submit]").click(
                  function(evt) { 
                    var vc = ndtable.rows().data()
                    var vm = vc.map(function(v) { return $(v[2]).text() })
                    for (let lname of vm.toArray()) {
                        $.ajax({url: escape(`videos/${lname}/edit`)+'?normalize', 
                                 async: false,
                                 success: function(result) { 
                                   $('#Normalize_form_results').html(result) } })
                    }
                  }) """


class SyncWithSeriesForm(SeriesForm):
    template = "sync_form.html"
    submital = Submital("Sync_Videos")

    def on_validated(self):    
        self.mstore.purge_cache(self.series)
        flask.flash(f"Resynced series {self.series.name}.")


class NewUserForm(MannaForm):
    template = "new_user_form.html"
    submital = Submital("Add")
    #username = fields.StringField('Username', [validators.Length(min=4, max=25)])
    email = EmailField('Email address', [validators.DataRequired(), validators.Email()])
    password = fields.PasswordField('New Password', 
        [ validators.DataRequired(),
          validators.EqualTo('confirm_pass', message='Passwords must match') ])
    confirm_pass = fields.PasswordField('Repeat Password')
    isadmin = fields.BooleanField('Admin', default=False)

    def on_validated(self):    
        form = flask.request.form
        pword = bcrypt.hashpw(form['password'].encode("utf-8"), bcrypt.gensalt())
        newuser = User( 
            email=form['email'],
            email_confirmed_at=datetime.utcnow(),
            password=pword)
        if 'isadmin' in  form:
            newuser.roles.append(Role.query.filter_by(name='Admin').first())
        newuser.roles.append(Role.query.filter_by(name='EndUser').first())
        mdb.session.add(newuser)
        mdb.session.commit()


class RegistrationForm(MannaForm):
    template = "confirm_registration.html"
    submital = Submital("Register", disabled=True)
    user_selection = fields.HiddenField()

    def __init__(self, users):
        super().__init__()
        self.table = UserTable(users, select={ 'style':'single'}) 
        self.template_vars.update(self.table.template_vars)
        self.scripts.extend(self.table.scripts)
        self.css = self.table.css

    @property
    def scriptage(self):
        return f"var dtable = {self.table.scriptage}\n" + \
                """dtable.on('select', (e,dt,type,idxs) => { 
                    var udata = dt.data()
                    var uregd = udata[2] == "True"
                    var uid = udata[3]
                    $('#user_selection').val(uid); 
                    $('#Register_submit').prop('disabled', uregd)
                    $('#Unregister_submit').prop('disabled', !uregd || uid == "1")
                    $('#Delete_submit').prop('disabled', uregd)
                })"""

    @property
    def submitals(self):
        return [ self.submital, 
                 Submital("Unregister", disabled=True), 
                 Submital("Delete", disabled=True)]

    @property
    def selected_user(self):
        sid = flask.request.form.get('user_selection', '')
        return User.query.filter_by(id=sid).first() if sid else None

    @property
    def operation(self):
        return flask.request.form['submission']

    def on_validated(self):    
        su = self.selected_user
        if su:
            su.active = (self.operation == "Register")
            if self.operation == "Delete":
                mdb.session.delete(su)
            mdb.session.commit()

