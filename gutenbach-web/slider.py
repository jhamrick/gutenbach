from tw.api import Widget, JSLink, CSSLink, js_function, js_callback, js_symbol
from tw.forms.fields import TextField
from tw.forms.validators import Pipe, Int

class UISlider(TextField):
    javascript = [
        JSLink(modname="sipbmp3web",filename="public/jquery/jquery-1.3.2.js"),
        JSLink(modname="sipbmp3web",filename="public/jquery/jquery-ui-personalized-1.6rc6.js"),
    ]
    template = "genshi:sipbmp3web.widgets.templates.slider"
    def __init__(self, *args, **kw):
        self.min = kw.pop("min")
        self.max = kw.pop("max")
        validator = Int(min=self.min, max=self.max)
        try:
            validator = Pipe(kw["validator"], validator)
        except KeyError:
            pass
        kw["validator"] = validator
        super(UISlider, self).__init__(*args, **kw)
    def update_params(self, d):
        super(TextField, self).update_params(d)
        if not getattr(d, "id", None):
            raise ValueError, "Slider must have id"
        container = '%s_container' % d.id
        self.add_call(js_callback('$("#%s").slider({ \
            min: %d, max: %d, step: 1, range: false, \
            value: $("#%s").val(), \
            slide: function (event, ui) { \
                jQuery("#%s").val(ui.value);\
            } \
            })' % (container, self.min, self.max, d.id, d.id)))
        jQuery = js_function('jQuery')
        input = jQuery("#%s" % d.id)
        self.add_call(input.css("display", "none"))

