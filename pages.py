import dominate as dom
import dominate.tags as tags
from dominate.util import raw

class Page(dom.document):
    
    def __init__(self, title, datatable=None):
        doc = super().__init__(title)
        if datatable:
            self.use_datatable(datatable)

    def use_datatable(self, table_id, version="1.10.20"):
        with self.head:
            tags.script(src="https://code.jquery.com/jquery-3.4.1.slim.min.js",
                        integrity="sha256-pasqAKBDmFT4eHoN2ndd6lN370kFiGUFyTiUHWhU7k8=",
                        crossorigin="anonymous")
            cdnbase = "https://cdn.datatables.net/{}".format(version)
            tags.link(rel="stylesheet", type="text/css", href=cdnbase + "/css/jquery.dataTables.css")
            tags.script(type="text/javascript", charset="utf8",
                        src=cdnbase + "/js/jquery.dataTables.js")
            tags.link(rel="stylesheet", type="text/css", href="static/data_tables.css")
            tags.script("$(document).ready( function () { $('#"
                         + "{}".format(table_id) 
                         + "').DataTable(); } );",
                         type="text/javascript")
