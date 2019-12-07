import dominate as dom
import web.vimeoresource as vr
from dateutil.parser import parse as dparse
from flask import Flask
from dominate import tags as tags

app = Flask(__name__)
app.config.from_object("web.config")

@app.route("/")
def root():
    doc = dom.document(title="Latest Lessons")
    with doc.head:
        use_datatables("1.10.20")
        tags.script("$(document).ready( function () { $('#latest_table').DataTable(); } );",
                    type="text/javascript")
    with doc:
        tags.div("Pleroma Bible Church")
        tags.div("Latest Lessons")
        with tags.table(id="latest_table"):
            with tags.thead():
                tags.th("Upload Date", _class="dt-head-left")
                tags.th("Name", _class="dt-head-left")
                tags.th("Duration", _class="dt-head-left")
                tags.th("Album", _class="dt-head-left")
            with tags.tbody():
                for x in vr.latest.values():
                    with tags.tr():
                        tags.td(str(dparse(x.upload_time).date()))
                        tags.td(tags.a(x.name, href=x.url))
                        tags.td(x.duration)
                        tags.td(tags.a(x.album.name, href=x.album.url))
    return doc.render()

@app.route("/videos/<vimeoid>")
def video_page(vimeoid):
    vid = vr.client.videoFor(vimeoid)
    return "TODO: Render vid {}".format(vid)

def use_datatables(version):
        tags.link(rel="stylesheet", type="text/css", 
                  href="https://cdn.datatables.net/{}/css/jquery.dataTables.css".format(version))
        tags.script(src="https://code.jquery.com/jquery-3.4.1.slim.min.js",
                    integrity="sha256-pasqAKBDmFT4eHoN2ndd6lN370kFiGUFyTiUHWhU7k8=",
                    crossorigin="anonymous")
        tags.script(type="text/javascript", charset="utf8",
                    src="https://cdn.datatables.net/{}/js/jquery.dataTables.js".format(version))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
