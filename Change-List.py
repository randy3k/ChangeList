import sublime, sublime_plugin
import os

# These variables are placed in globals so that
# they will not be destoyed when reloading perferences
# to store edited positions
if not 'EPOS' in globals(): EPOS = {}
# to store num of lines
if not 'FILESIZE' in globals(): FILESIZE = {}
# to store current index
if not 'CURRIDX' in globals(): CURRIDX = {}
# to store last multi cursors' positions
if not 'MCURPOS' in globals(): MCURPOS = {}
# to store row of last eidted postision
if not 'LASTROW' in globals(): LASTROW = {}

class CommandManager():
    def GoToChange(self, i):
        view = self.view
        vid = view.id()
        if (i<0)| (i>len(EPOS[vid])-1): return
        CURRIDX[vid] = i
        pos = EPOS[vid][i]
        view.sel().clear()
        view.show(pos)
        view.sel().add(pos)

        # to reactivate sublime_plugin.WindowCommand.on_selection_modified()
        # useful for plugin - SublimeBlockCursor
        if view.settings().get('command_mode'):
            view.run_command("enter_insert_mode")
            view.run_command("exit_insert_mode")

        sublime.status_message("@Change List [%s]" % CURRIDX[vid] )


class JumpToChangeCommand(sublime_plugin.TextCommand,CommandManager):
    def run(self, _, **kwargs):
        view = self.view
        vid = view.id()
        if not EPOS.has_key(vid): return
        if not EPOS[vid]: return
        # if the cursor has moved away from the recent edited location, set move = 0
        curr_pos = view.sel()[0].end()
        if not kwargs.has_key('index'):
            move = kwargs['move']
            if CURRIDX[vid]==0 and move==1:
                if abs(curr_pos - EPOS[vid][0])>1: move = 0
            self.GoToChange(CURRIDX[vid]+move)
        else:
            self.GoToChange(kwargs['index'])

class ShowChangeList(sublime_plugin.WindowCommand,CommandManager):
    def run(self):
        self.view = self.window.active_view()
        view = self.view
        vid = view.id()
        if not EPOS.has_key(vid): return
        if not EPOS[vid]: return
        change_list = [ "[%2d] Line %3d: %s" % (i, view.rowcol(pos)[0]+1,
            view.substr(view.line(pos))) for i,pos in enumerate(EPOS[vid])]
        self.window.show_quick_panel(change_list, self.on_done)

    def on_done(self, action):
        if action==-1: return
        self.GoToChange(action)

class ClearChangeList(sublime_plugin.WindowCommand,CommandManager):
    def run(self):
        self.view = self.window.active_view()
        try:
            fname = os.path.basename(self.view.file_name())
        except:
            fname = "untitled"
        self.window.show_quick_panel([fname, "All files"], self.on_done)

    def on_done(self, action):
        if action==0:
            vid = self.view.id()
            if EPOS.has_key(vid): EPOS[vid] = []
            try:
                vname = self.view.file_name()
            except: return
            settings = sublime.load_settings('%s.sublime-settings' % __name__)
            if settings.has(vname): settings.erase(vname)
            sublime.save_settings('%s.sublime-settings' % __name__)
            sublime.status_message("Clear Change List (this file) successfually.")
        elif action==1:
            for key in EPOS: EPOS[key]  = []
            try:
                path = os.path.join(sublime.packages_path(), "User" , '%s.sublime-settings' % __name__)
                if os.path.exists(path): os.remove(path)
            except (OSError, IOError):
                sublime.error_message("Error occurred while clearing Change List!")
                return
            sublime.status_message("Clear Change List (all file) successfually.")


class ChangeListener(sublime_plugin.EventListener):

    def insert_curr_pos(self, view, ):
        vid = view.id()
        curr_pos = map(lambda s: s.end(), view.sel())
        curr_row = view.rowcol(curr_pos[0])[0]
        if EPOS[vid]:
            if not LASTROW.has_key(vid): LASTROW[vid] = curr_row
            if abs(curr_row - LASTROW[vid])>1:
                EPOS[vid].insert(0,curr_pos[0])
            else:
                EPOS[vid][0] = curr_pos[0]
            if len(EPOS[vid])>50: EPOS[vid].pop()
        else:
            EPOS[vid] = [curr_pos[0]]
        LASTROW[vid] = curr_row

    def update_pos(self, view):
        vid = view.id()
        curr_pos = map(lambda s: s.end(), view.sel())
        file_size = view.size()
        if not FILESIZE.has_key(vid): FILESIZE[vid] = file_size
        deltas = map(lambda x,y: x-y, curr_pos, MCURPOS[vid])
        deltas = [long(x - deltas[i-1]) for i,x in enumerate(deltas) if i>0]
        deltas = [long(file_size-FILESIZE[vid]-sum(deltas))] + deltas

        for i  in range(len(curr_pos)):
            # drop positions
            delta = deltas[i]
            if delta<0:
                EPOS[vid] = [pos for pos in EPOS[vid] if pos<=curr_pos[i] or pos>=curr_pos[i]-delta]

            # update positions
            if delta!=0 :
                EPOS[vid] = [pos+delta if pos > MCURPOS[vid][i] else pos for pos in EPOS[vid]]
                MCURPOS[vid] = [pos+delta if pos > MCURPOS[vid][i] else pos for pos in MCURPOS[vid]]

        FILESIZE[vid] = file_size
        # drop invalid positions
        EPOS[vid] = [pos for pos in EPOS[vid] if pos>=0 and pos<=file_size]

    def on_load(self, view):
        vid = view.id()
        vname = view.file_name()
        settings = sublime.load_settings('%s.sublime-settings' % __name__)
        if settings.has(vname):
            if settings.get(vname):
                try:
                    EPOS[vid] = [long(item) for item in settings.get(vname).split(",")]
                except:
                    EPOS[vid] = []
        if not EPOS.has_key(vid): EPOS[vid] = []
        CURRIDX[vid] = 0

    def on_selection_modified(self, view):
        vid = view.id()
        # get the current multi cursor locations
        MCURPOS[vid] = map(lambda s: s.end(), view.sel())

    def on_modified(self, view):
        if view.is_scratch() or view.settings().get('is_widget'): return
        vid = view.id()
        # reset current index
        CURRIDX[vid] = 0
        # update saved postions
        if not EPOS.has_key(vid): EPOS[vid]=[]
        if EPOS[vid]: self.update_pos(view)
        # insert current position
        self.insert_curr_pos(view)
        # print map(lambda x: [x[0]+1,x[1]+1], map(lambda p: view.rowcol(p), EPOS[vid]))
        # print EPOS[vid]


    def on_post_save(self, view):
        vid = view.id()
        vname = view.file_name()
        settings = sublime.load_settings('%s.sublime-settings' % __name__)
        settings.set(vname, ",".join(map(str, EPOS[vid])))
        sublime.save_settings('%s.sublime-settings' % __name__)

    def on_close(self, view):
        vid = view.id()
        if EPOS.has_key(vid): EPOS.pop(vid)
        if FILESIZE.has_key(vid): FILESIZE.pop(vid)
        if CURRIDX.has_key(vid): CURRIDX.pop(vid)
        if MCURPOS.has_key(vid): MCURPOS.pop(vid)
        if LASTROW.has_key(vid): LASTROW.pop(vid)