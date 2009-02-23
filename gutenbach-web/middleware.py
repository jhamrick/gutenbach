"""TurboGears middleware initialization"""
from sipbmp3web.config.app_cfg import base_config
from sipbmp3web.config.environment import load_environment
import subprocess, os
from pylons import config

#Use base_config to setup the necessary WSGI App factory. 
#make_base_app will wrap the TG2 app with all the middleware it needs. 
make_base_app = base_config.setup_tg_wsgi_app(load_environment)

class FastCGIFixMiddleware(object):
    """Remove dispatch.fcgi from the SCRIPT_NAME
    
    mod_rewrite doesn't do a perfect job of hiding it's actions to the
    underlying script, which causes TurboGears to get confused and tack
    on dispatch.fcgi when it really shouldn't. This fixes that problem as a
    Middleware that fiddles with the appropriate environment variable
    before any processing takes place.
    """
    def __init__(self, app, global_conf=None):
        self.app = app
    def __call__(self, environ, start_response):
        environ['SCRIPT_NAME'] = environ['SCRIPT_NAME'].replace('/dispatch.fcgi', '')
        return self.app(environ, start_response)

class KinitMiddleware(object):
    """Performs Kerberos authentication with a keytab"""
    def __init__(self, app, global_conf=None):
        self.app = app
        self.keytab = config["keytab"]
    def __call__(self, environ, start_response):
        if self.keytab:
            subprocess.call(["/usr/kerberos/bin/kinit", "ezyang/extra", "-k", "-t", self.keytab])
        return self.app(environ, start_response)

def make_app(global_conf, full_stack=True, **app_conf):
    app = make_base_app(global_conf, full_stack=True, **app_conf)
    app = FastCGIFixMiddleware(app, global_conf)
    app = KinitMiddleware(app, global_conf)
    return app


