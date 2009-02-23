"""Main Controller"""
from sipbmp3web.lib.base import BaseController
from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _
#from tg import redirect, validate
from sipbmp3web.model import DBSession, metadata
from sipbmp3web.controllers.error import ErrorController
from sipbmp3web import model
from catwalk.tg2 import Catwalk
from repoze.what import predicates
from sipbmp3web.controllers.secure import SecureController
from remctl import remctl

class RootController(BaseController):
    admin = Catwalk(model, DBSession)
    error = ErrorController()

    @expose('sipbmp3web.templates.index')
    def index(self):
        out = dict()
        out["volume"] = remctl("zsr", command=["v", "get"]).stdout
        return out

    @expose('sipbmp3web.templates.about')
    def about(self):
        return dict()

