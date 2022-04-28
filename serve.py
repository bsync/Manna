import multiprocessing, gunicorn.app.wsgiapp as wsgi
import sys

class MannaApp(wsgi.WSGIApplication):

    def __init__(self, **options):
        self.options = options
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        if 'init_modules' not in globals(): # on first run: note which modules were initially loaded
            init_modules = sys.modules.keys()
        else: # on subsequent runs: remove all but the initially loaded modules
            for m in sys.modules.keys(  ):
                if m not in init_modules:
                    del(sys.modules[m])
        import manna
        return manna.Manna()

if __name__ == '__main__':
	
	MannaApp(
            bind='%s:%s' % ('0.0.0.0', '8001'),
            #max_requests=1,
            timeout=480, 
            certfile="/etc/letsencrypt/live/pleromabiblechurch.org/fullchain.pem",
            keyfile="/etc/letsencrypt/live/pleromabiblechurch.org/privkey.pem",
            raw_env=['SCRIPT_NAME=/manna'],
            workers=1,  #(multiprocessing.cpu_count() * 2) + 1
            reload=True,
        ).run()

