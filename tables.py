from flask import url_for

class DataTable(object):
    css = [ 
        "https://cdn.datatables.net/r/ju-1.11.4/jqc-1.11.3,dt-1.10.8/datatables.min.css",
        "https://cdn.datatables.net/select/1.3.3/css/select.dataTables.min.css", 
        "tables.css"] 
    scripts = [ 
        "https://cdn.datatables.net/r/ju-1.11.4/jqc-1.11.3,dt-1.10.8/datatables.min.js",
        "https://cdn.datatables.net/select/1.3.3/js/dataTables.select.min.js", ]
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.kwargs.setdefault('order', [[0,"desc"]]) 
        self.kwargs.setdefault('processing', "true") 

    @property
    def scriptage(self):
        dtargs = ",".join([ f' {x}: {y}' for x,y in self.kwargs.items() ])
        return f"""var {self.id} = $('#{self.id}').DataTable({{{dtargs}}}) """

    _tblcnt = 0
    @property
    def id(self):
        if not hasattr(self, 'tblnum'):
            self.tblnum = DataTable._tblcnt
            DataTable._tblcnt += 1
        return f"{self.__class__.__name__}_table{self.tblnum}"

    @property
    def selectable(self):
        return 'select' in self.kwargs

    @selectable.setter
    def selectable(self, value):
        if value:
            self.kwargs['select'] = { 'style':value} #, 'selector':'td:first-child' }
            #self.kwargs['columnDefs'] = [{ "className":"select-checkbox", "targets":0 }]
        else:
            del self.kwargs['select']

    def __new__(_cls, *args, **kwargs):
        # Disable base class tag decoration logic which is otherwise being
        # inadvertently triggered by singular callable args such as are 
        # typically used by subclasses of DataTable and which tend to pass
        # arguments like mongo queryset results which are callable...
        return object.__new__(_cls)


class CatalogTable(DataTable):
    template = "catalog_table.html"
    def __init__(self, catalog, *args, **kwargs):
        kwargs.setdefault('order', [[2,"asc"]])
        super().__init__(*args, **kwargs)
        self.template_vars = dict(catalog=catalog, tbl_id=self.id)


class VideoTable(DataTable):
    template = "vid_table.html"
    def __init__(self, vids, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_vars = dict(vids=vids, tbl_id=self.id)


class UserTable(DataTable):
    def __init__(self, users, *args, **kwargs):
        super().__init__(*args,  **kwargs)
        self.refresh(users)

    def refresh(self, users):
        self.head.clear()
        with self.head:
            tags.th("Name", _class="dt-head-left")
            tags.th("Email", _class="dt-head-left")
            tags.th("Active", _class="dt-head-left")
        self.body.clear()
        with self.body:
            @tags.tr
            def _row(u):
                tags.td(f"{u.name}")
                tags.td(f"{u.email}")
                tags.td(f"{u.is_active}")
            for u in users: 
                _row(u)
