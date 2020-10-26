import os, vimeo, json

vc = vimeo.VimeoClient(os.getenv('VIMEO_TOKEN'),
                       os.getenv('VIMEO_CLIENT_ID'),
                       os.getenv('VIMEO_CLIENT_SECRET'))

def get(url, **kwargs):
    return checked(vc.get(url, params=kwargs))

def post(url, **kwargs):
    return checked(vc.post(url, data=kwargs))

def put(url, **kwargs):
    return checked(vc.put(url, data=kwargs))

def delete(url, **kwargs):
    return checked(vc.delete(url, params=kwargs))

def checked(resp):
    class VimeoException(Exception):
        pass
    if resp.status_code > 399:
        raise VimeoException(f"Vimeo Response: {resp.json()}")
    return resp

