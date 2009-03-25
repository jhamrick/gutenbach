"""Main Controller"""
from sipbmp3web.lib.base import BaseController
from tg import expose, flash, require, url, request, redirect, validate
from pylons.i18n import ugettext as _
from pylons import config
#from tg import redirect, validate
from sipbmp3web.model import DBSession, metadata
from sipbmp3web.controllers.error import ErrorController
from sipbmp3web import model
from repoze.what import predicates
from sipbmp3web.controllers.secure import SecureController
from remctl import remctl
import tw.forms as twf
from sipbmp3web.widgets.slider import UISlider

volume_form = twf.TableForm('volume_form', action='volume', children=[
    UISlider('volume', min=1, max=31, validator=twf.validators.NotEmpty())
])

class RootController(BaseController):
    error = ErrorController()

    @expose('sipbmp3web.templates.index')
    def index(self, **kw):
        server = config['sipbmp3.server']
        out = dict(page="index")
        volume = int(remctl(server, command=["volume", "get"]).stdout.rstrip())
        playing = remctl(server, command=["status", "get"]).stdout
        # Todo: add better parsing
        if not playing: playing = "Nothing playing"
        if not "volume" in kw: kw["volume"] = volume
        return dict(
                    page="index",
                    playing=playing,
                    volume=volume,
                    volume_form=volume_form,
                    volume_data=kw,
                )

    @validate(form=volume_form, error_handler=index)
    @expose()
    def volume(self, **kw):
        remctl(server, command=["volume", "set", kw["volume"]])
        redirect('index')

    @expose('sipbmp3web.templates.about')
    def about(self):
        return dict(page="about")

    @expose('sipbmp3web.templates.todo')
    def todo(self):
        return dict(page="todo")

