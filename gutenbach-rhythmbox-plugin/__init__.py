import rb
import gtk
import urlparse
import urllib
import subprocess

menu_ui = """
<ui> 
  <popup name="BrowserSourceViewPopup"> 
    <menuitem name="Pikamp3" action="SendToPikamp3"/>
  </popup>
</ui>
"""
class Pikamp3Plugin(rb.Plugin):
    def __init__(self):
        rb.Plugin.__init__(self)

    def activate(self, shell):
        self.shell = shell
        # Create action for sending a track to pikamp3
        action = gtk.Action('SendToPikamp3', _('Send to pikamp3'),
                _("Queue selected tracks to the pikamp3 server."),
                "")
        action.connect('activate', self.pikamp3_action, shell)
        action_group = gtk.ActionGroup('Pikamp3ActionGroup')
        action_group.add_action(action)
        manager = shell.get_ui_manager()
        manager.insert_action_group(action_group)
        manager.add_ui_from_string(menu_ui)

    def deactivate(self, shell):
        del self.shell

    def pikamp3_action(self, action, shell):
        source = shell.get_property("selected-source")
        for entry in source.get_entry_view().get_selected_entries():
            uri = entry.get_playback_uri()
            p = urlparse.urlparse(urllib.unquote(uri))
            if p.scheme == "file":
                path = p.path
                command = 'lpr -P pikamp3@lbsg.mit.edu "%s"' % path
                print command
                subprocess.Popen(command, shell=True)



