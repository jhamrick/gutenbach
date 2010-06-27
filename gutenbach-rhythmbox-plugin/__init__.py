"""
This module implements a Rhythmbox plugin that sends selected track to a
printer queue. It's meant to be used with gutenbach, a music spooling printer
server.

The plugin uses lpr to send the files to gutenbach.
"""
import gtk
import rb
import subprocess
import urllib
import urlparse

# UI Change is an extra item added to right-click menu when clicking on tracks
popup_ui = """
<ui> 
  <popup name="BrowserSourceViewPopup"> 
    <menuitem name="Gutenbach" action="SendToGutenbach"/>
  </popup>
</ui>
"""
class GutenbachPlugin(rb.Plugin):
    def __init__(self):
        rb.Plugin.__init__(self)

    def activate(self, shell):
        """Adds a new item to the right-click menu which allows
        sending music files to the gutenbach server.
        """
        self.shell = shell
        # Create action for sending a track to gutenbach
        action = gtk.Action('SendToGutenbach', _('Send to gutenbach'),
                _("Queue selected tracks to the gutenbach server."),
                "")
        action.connect('activate', self.gutenbach_action, shell)
        action_group = gtk.ActionGroup('GutenbachActionGroup')
        action_group.add_action(action)
        manager = shell.get_ui_manager()
        manager.insert_action_group(action_group)
        manager.add_ui_from_string(popup_ui)

        # Default configuration options
        self.printer = "printername"
        self.printer_host = "hostname"

    def deactivate(self, shell):
        del self.shell

    def gutenbach_action(self, action, shell):
        """An action called when the user clicks the right-click menu item
        to send a track to gutenbach.
        This function calls an instance of lpr for each file to be added.
        """
        source = shell.get_property("selected-source")
        # For each track currently selected in the song browser
        for entry in source.get_entry_view().get_selected_entries():
            # Only play files that are stored on the user's computer
            uri = entry.get_playback_uri()
            p = urlparse.urlparse(urllib.unquote(uri))
            if p.scheme == "file":
                path = p.path
                if self.printer_host:
                    printer = '@'.join([self.printer, self.printer_host])
                else:
                    printer = self.printer
                command = 'lpr -P %s "%s"' % (printer, path)
                print "About to run command '%s'" % command
                subprocess.Popen(command, shell=True)

