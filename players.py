
class VideoPlayer(object):
    template = "vid_player.html"
    scripts = ["https://player.vimeo.com/api/player.js",
               "https://code.jquery.com/jquery-3.6.0.min.js",
               "jquery.fitvids.js"]
    def __init__(self, vid, *args, **kwargs):
        self.template_vars = dict(vid=vid)
        self.scriptage = """
            new Vimeo.Player('player')
            $("#player").fitVids()
        """
