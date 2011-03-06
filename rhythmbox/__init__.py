from __future__ import division

import rb
import gtk, gtk.glade, gconf
import gobject
import sys, os
import locale, datetime, time
import subprocess
import urllib
import urlparse

#fade_steps = 50

ui_str = '''
<ui> 
  <popup name="BrowserSourceViewPopup"> 
    <menuitem name="Gutenbach" action="GutenbachDialog"/>
  </popup>
</ui>
'''

class GutenbachPlugin(rb.Plugin):
    def __init__ (self):
        rb.Plugin.__init__ (self)

    def activate (self, shell):
        data = dict()
        manager = shell.get_player().get_property('ui-manager')
        self.shell = shell
        action = gtk.Action('GutenbachDialog', _('_Send to gutenbach'), _('Spool song to gutenbach server'), None);
        action.connect('activate', self.show_conf_dialog)
        data['action_group'] = gtk.ActionGroup('GutenbachGroup')
        data['action_group'].add_action(action)
        manager.insert_action_group(data['action_group'], 0)

        data['ui_id'] = manager.add_ui_from_string(ui_str)
        manager.ensure_update()
        shell.set_data('GutenbachInfo', data)



    def deactivate(self, shell):
        self.toolbar.remove(self.separator)
        data = shell.get_data('GutenbachInfo')
        manager = shell.get_player().get_property('ui-manager')
        manager.remove_ui(data['ui_id'])
        del self.player
        del self.separator
	del self.toolbar
        del self.shell

    def show_conf_dialog(self, action):
        self.wTree = gtk.glade.XML(self.find_file('gutenbach-rhythmbox-2.glade'))
        widgets = {}
        widgets['gutenbach-dialog'] = self.wTree.get_widget('gutenbach-dialog')
        dic = { 
            "on_gutenbach-ok_clicked" : self.process,
            "on_windowMain_destroy" : self.quit,
            }

        self.wTree.signal_autoconnect( dic )

        # Fix proper Dialog placements
        widgets['gutenbach-dialog'].set_transient_for(self.shell.props.window)

        def gconf_path(key):
            return '%s%s' % (gconf_plugin_path, key)


        widget = None
	try:
		memf = open('savedqueue','r+')
	except IOError:
		memf = file('savedqueue', 'wt')
		memf.close()
	memf = open('savedqueue','r+')
	memLine = memf.readline()
	if memLine != "":
		left = memLine
		right = memf.readline()
		self.wTree.get_widget("gutenbach-printer-entry").set_text(left.rstrip('\n'))
		self.wTree.get_widget("gutenbach-host-entry").set_text(right.rstrip('\n'))
	memf.close()
        widgets['gutenbach-dialog'].run()
	self.process(widget)
        widgets['gutenbach-dialog'].destroy()
    def process(self, widget):
        memf = open('savedqueue','r+')
	printerMem = (self.wTree.get_widget("gutenbach-printer-entry").get_text())
	hostMem = (self.wTree.get_widget("gutenbach-host-entry").get_text())
	memf.write(printerMem)
	memf.write("\n")
	memf.write(hostMem)
	memf.write("\n")
	memf.close();
	self.process_songs(printerMem, hostMem)
     # stuff that does things  
    def process_songs(self, printer, host):
        source = self.shell.get_property("selected-source")
        # For each track currently selected in the song browser
        for entry in source.get_entry_view().get_selected_entries():
            # Only play files that are stored on the user's computer
            uri = entry.get_playback_uri()
            p = urlparse.urlparse(urllib.unquote(uri))
            if p.scheme == "file":
                path = p.path
                if host:
                    print "there is a host"
                   # printer = '@'.join([printer, printer_host])
        
                printer = printer
                #command = 'gbr "%s"' % (path)
                command = 'lpr -H%s -P%s "%s"' % (host,printer, path)
                print "About to run command '%s'" % command
                subprocess.Popen(command, shell=True)
    def quit(self, widget):
        return
                          
