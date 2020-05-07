from flask_executor import Executor

_ex = Executor()
futures = _ex.futures
fk = None

def init_flask(app):
    _ex.init_app(app)

status = "idle"

def submit_stored(name, func, *args):
    _ex.submit_stored(name, func, *args)
