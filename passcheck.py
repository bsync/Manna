import sys

class algo:
    def __call__(self, url, password):
        raise(RuntimeError("Put custom password lookup logic here."))

sys.modules[__name__] = algo()
