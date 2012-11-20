import sublime, sublime_plugin
import os

# These variables are placed in globals so that
# they will not be destoyed when reloading perferences
# to store edited positions
if not 'EPOS' in globals(): EPOS = {}
# to store num of lines
if not 'FILENOL' in globals(): FILENOL = {}
# to store current index
if not 'CURRIDX' in globals(): CURRIDX = {}
# to store last multi cursors' positions
if not 'MCURPOS' in globals(): MCURPOS = {}

class CommandManager():
    def GoToChange(self, i):
        view = self.view
        vid = view.id()
        if (i<0)| (i>len(EPOS[vid])-1): return
        CURRIDX[vid] = i
        pos = EPOS[vid][i]
        region = view.text_point(pos[0],pos[1])
        view.sel().clear()
        view.show(region)
        view.sel().add(region)

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
        curr_pos = view.rowcol(view.sel()[0].end())
        if not kwargs.has_key('index'):
            move = kwargs['move']
            if CURRIDX[vid]==0 and move==1:
                if (curr_pos[0] != EPOS[vid][0][0]): move = 0
                elif abs(curr_pos[1] - EPOS[vid][0][1])>1: move = 0
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
        change_list = [ "[%2d] Line %3d: %s" % (i, item[0]+1,
            view.substr(view.line(view.text_point(item[0],item[1])))) for i,item in enumerate(EPOS[vid])]
        self.window.show_quick_panel(change_list, self.on_done)

    def on_done(self, action):
        if action==-1: return
        print(self.view.id())
        # view = self.window.active_view()
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
            try:
                vname = self.view.file_name()
            except: return
            settings = sublime.load_settings('%s.sublime-settings' % __name__)
            if settings.has(vname): settings.erase(vname)
            sublime.save_settings('%s.sublime-settings' % __name__)
            sublime.status_message("Clear Change List (this file) successfually.")
            if EPOS.has_key(vid): EPOS[vid] = []
        elif action==1:
            try:
                path = os.path.join(sublime.packages_path(), "User" , '%s.sublime-settings' % __name__)
                if os.path.exists(path): os.remove(path)
            except (OSError, IOError):
                sublime.error_message("Error occurred while clearing Change List!")
                return
            sublime.status_message("Clear Change List (all file) successfually.")
            for key in EPOS: EPOS[key]  = []

class ChangeListener(sublime_plugin.EventListener):

    def insert_curr_pos(self, view, ):
        vid = view.id()
        curr_pos = map(int, view.rowcol(view.sel()[0].end()))
        if EPOS[vid]:
            if abs(EPOS[vid][0][0] - curr_pos[0])>1:
                EPOS[vid].insert(0,curr_pos)
            else:
                EPOS[vid][0] = curr_pos
            if len(EPOS[vid])>50: EPOS[vid].pop()
        else:
            EPOS[vid] = [curr_pos]

    def update_pos(self, view):
        vid = view.id()
        curr_pos = map(lambda s: map(int, view.rowcol(s.end())) ,view.sel())
        file_nol = view.rowcol(view.size())[0]
        if not FILENOL.has_key(vid): FILENOL[vid] = file_nol
        # if num of lines changes
        deltas = map(lambda x,y: x[0]-y[0], curr_pos, MCURPOS[vid])
        deltas = [int(x - deltas[i-1]) for i,x in enumerate(deltas) if i>0]
        deltas = [int(file_nol-FILENOL[vid]-sum(deltas))] + deltas
        cdeltas = map(lambda x,y: x[1]-y[1], curr_pos, MCURPOS[vid])
        # print(deltas)
        for i  in range(len(curr_pos)):
            # drop rows
            delta = deltas[i]
            if delta<0 :
                EPOS[vid] = [pos for pos in EPOS[vid] if pos[0]<curr_pos[i][0] or pos[0]>MCURPOS[vid][i][0]]
            # update rows
            if delta!=0 :
                EPOS[vid] = [[pos[0]+delta, pos[1]] if pos[0] > MCURPOS[vid][i][0] \
                    else pos for pos in EPOS[vid]]
                MCURPOS[vid] = [[pos[0]+delta, pos[1]] if pos[0] > MCURPOS[vid][i][0] \
                    else pos for pos in MCURPOS[vid]]

            cdelta = cdeltas[i]
            # drop cols
            if cdelta<0 :
                EPOS[vid] = [pos for pos in EPOS[vid] if \
                    pos[0]!=MCURPOS[vid][i][0] or pos[1]<curr_pos[i][1] or pos[1]>MCURPOS[vid][i][1]]
            # update cols
            if cdelta!=0 :
                EPOS[vid] = [[pos[0], pos[1]+cdelta] if pos[0]==curr_pos[i][0] and pos[1] > curr_pos[i][1] \
                    else pos for pos in EPOS[vid]]

        # drop position if position is not valid
        eol = lambda pos: view.rowcol(view.line(view.text_point(pos[0],0)).end())[1]
        EPOS[vid] = [[pos[0],eol(pos)] if eol(pos)<pos[1] else pos for pos in EPOS[vid] if pos[0]>=0 and pos[0]<=file_nol]
        # update num of lines
        FILENOL[vid] = file_nol

    def on_load(self, view):
        vid = view.id()
        vname = view.file_name()
        settings = sublime.load_settings('%s.sublime-settings' % __name__)
        if settings.has(vname):
            if settings.get(vname):
                EPOS[vid] = [map(int, item.split(",")) for item in settings.get(vname).split("|")]
        if not EPOS.has_key(vid): EPOS[vid] = []
        CURRIDX[vid] = 0

    def on_selection_modified(self, view):
        vid = view.id()
        # get the current multi cursor locations
        MCURPOS[vid] = map(lambda s: map(int, view.rowcol(s.end())) ,view.sel())

    def on_modified(self, view):
        # print(globals()w)
        if view.is_scratch() or view.settings().get('is_widget'): return
        vid = view.id()
        # reset current index
        CURRIDX[vid] = 0
        # update saved postions
        if not EPOS.has_key(vid): EPOS[vid]=[]
        if EPOS[vid]: self.update_pos(view)
        # insert current position
        self.insert_curr_pos(view)
        # print(map(lambda x: [x[0]+1,x[1]+1], EPOS[vid]))


    def on_post_save(self, view):
        vid = view.id()
        vname = view.file_name()
        settings = sublime.load_settings('%s.sublime-settings' % __name__)
        settings.set(vname, "|".join([",".join(map(str, item)) for item in EPOS[vid]]))
        sublime.save_settings('%s.sublime-settings' % __name__)

    def on_close(self, view):
        vid = view.id()
        if EPOS.has_key(vid): EPOS.pop(vid)
        if FILENOL.has_key(vid): FILENOL.pop(vid)
        if CURRIDX.has_key(vid): CURRIDX.pop(vid)
        if MCURPOS.has_key(vid): MCURPOS.pop(vid)