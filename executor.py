from flask_executor import Executor
import dominate.tags as tags

_ex = Executor()

futures = _ex.futures

status = ''

def init_flask(app):
    _ex.init_app(app)

def monitor(func, *args):
    def watcher(yielder, *args):
        global status
        for ystat in yielder(*args):
            status = ystat
            print(f"Setting executor status to {status}")
        status = ""
    _ex.submit_stored('monitor', watcher, func, *args)
    return f"Monitoring {func.__name__} for completion"
    
