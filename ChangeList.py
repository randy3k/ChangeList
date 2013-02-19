import sublime, sublime_plugin
import os

# G_REGISTER is placed in global so that
# it will not be destoyed when reloading perferences

if not 'G_REGISTER' in globals(): G_REGISTER = {}

class PosStorage():
    def __init__(self, view, saved_pos=[]):
        self.vid = view.id()
        self.saved_pos = saved_pos
        self.curr_idx = 0
        self.last_row = view.rowcol(view.sel()[0].end())[1]
        self.file_size = view.size()
        self.old_pos = map(lambda s: s.end(), view.sel())

class CommandManager():
    def GoToChange(self, view, i):
        vid = view.id()
        if i<0 or i>len(G_REGISTER[vid].saved_pos)-1: return
        G_REGISTER[vid].curr_idx = i
        pos = G_REGISTER[vid].saved_pos[i]
        view.sel().clear()
        view.show(pos)
        view.sel().add(pos)

        # to reactivate sublime_plugin.WindowCommand.on_selection_modified()
        # useful for plugin - SublimeBlockCursor
        if view.settings().get('command_mode'):
            view.run_command("enter_insert_mode")
            view.run_command("exit_insert_mode")
        else:
            view.run_command("move", {"by": "characters", "forward" : False})
            view.run_command("move", {"by": "characters", "forward" : True})

        sublime.status_message("@Change List [%s]" % G_REGISTER[vid].curr_idx )


class JumpToChangeCommand(sublime_plugin.TextCommand, CommandManager):
    def run(self, _, **kwargs):
        view = self.view
        vid = view.id()
        if not G_REGISTER.has_key(vid): return
        if not G_REGISTER[vid].saved_pos: return
        # if the cursor has moved away from the recent edited location, set move = 0
        curr_pos = view.sel()[0].end()
        if not kwargs.has_key('index'):
            move = kwargs['move']
            if G_REGISTER[vid].curr_idx==0 and move==1:
                if abs(curr_pos - G_REGISTER[vid].saved_pos[0])>1: move = 0
            self.GoToChange(view, G_REGISTER[vid].curr_idx + move)
        else:
            self.GoToChange(view, kwargs['index'])

class ShowChangeList(sublime_plugin.WindowCommand, CommandManager):
    def run(self):
        view = self.window.active_view()
        vid = view.id()
        if not G_REGISTER.has_key(vid): return
        if not G_REGISTER[vid].saved_pos: return
        change_list = [ "[%2d] Line %3d: %s" % (i, view.rowcol(pos)[0]+1,
            view.substr(view.line(pos))) for i,pos in enumerate(G_REGISTER[vid].saved_pos)]
        self.window.show_quick_panel(change_list, self.on_done)

    def on_done(self, action):
        view = self.window.active_view()
        if action==-1: return
        self.GoToChange(view, action)

class ClearChangeList(sublime_plugin.WindowCommand, CommandManager):
    def run(self):
        self.view = self.window.active_view()
        try:
            fname = os.path.basename(self.view.file_name())
        except:
            fname = "untitled"
        self.window.show_quick_panel([fname, "All files"], self.on_done)

    def on_done(self, action):
        global G_REGISTER
        if action==0:
            vid = self.view.id()
            if G_REGISTER.has_key(vid): G_REGISTER.pop(vid)
            vname = self.view.file_name()
            settings = sublime.load_settings('%s.sublime-settings' % __name__)
            if vname and settings.has(vname): settings.erase(vname)
            sublime.save_settings('%s.sublime-settings' % __name__)
            sublime.status_message("Clear Change List (this file) successfully.")
        elif action==1:
            G_REGISTER = {}
            path = os.path.join(sublime.packages_path(), "User" , '%s.sublime-settings' % __name__)
            if os.path.exists(path): os.remove(path)
            sublime.status_message("Clear Change List (all file) successfully.")


class ChangeListener(sublime_plugin.EventListener):

    def insert_curr_pos(self, view, ):
        vid = view.id()
        G = G_REGISTER[vid]
        curr_pos = map(lambda s: s.end(), view.sel())
        curr_row = view.rowcol(curr_pos[0])[0]
        if G.saved_pos:
            if abs(curr_row - G.last_row)>1:
                G.saved_pos.insert(0,curr_pos[0])
            else:
                G.saved_pos[0] = curr_pos[0]
            if len(G.saved_pos)>50: G.saved_pos.pop()
        else:
            G.saved_pos = [curr_pos[0]]
        # update last_row
        G.last_row = curr_row

    def update_pos(self, view):
        vid = view.id()
        G = G_REGISTER[vid]
        if not G.saved_pos: return
        curr_pos = map(lambda s: s.end(), view.sel())
        old_pos = G.old_pos
        file_size = view.size()
        # probelms can be created if number of selections changes
        if len(curr_pos)==len(G.old_pos):
            deltas = map(lambda x,y: x-y, curr_pos, G.old_pos)
            deltas = [long(x - deltas[i-1]) for i,x in enumerate(deltas) if i>0]
            deltas = [long(file_size-G.file_size-sum(deltas))] + deltas

            for i  in reversed(range(len(curr_pos))):
                #  delete positions in previous selection
                delta = deltas[i]
                if delta<0:
                    G.saved_pos = [pos for pos in G.saved_pos if pos<curr_pos[i] or pos>=curr_pos[i]-delta]

                # update positions
                if delta!=0 :
                    G.saved_pos = [pos+delta if pos >= old_pos[i] else pos for pos in G.saved_pos]
        else:
            # if not, do the best to update position
            print "Warnings from Change List: number of selections change"
            delta = long(file_size-G.file_size)
            if delta!=0 :
                G.saved_pos = [pos+delta if pos >= curr_pos[0] else pos for pos in G.saved_pos]

        # update file size
        G.file_size = file_size
        # drop invalid positions
        G.saved_pos = [pos for pos in G.saved_pos if pos>=0 and pos<=file_size]

    def on_load(self, view):
        vid = view.id()
        vname = view.file_name()
        settings = sublime.load_settings('%s.sublime-settings' % __name__)
        if vname and settings.has(vname):
            try:
                saved_pos = [long(item) for item in settings.get(vname).split(",")]
            except:
                saved_pos = []
        else:
            saved_pos = []
        if not G_REGISTER.has_key(vid): G_REGISTER[vid] = PosStorage(view, saved_pos)

    def on_selection_modified(self, view):
        vid = view.id()
        if not G_REGISTER.has_key(vid): G_REGISTER[vid] = PosStorage(view)
        # get the current multi cursor locations
        G_REGISTER[vid].old_pos = map(lambda s: s.end(), view.sel())

    def on_modified(self, view):
        if view.is_scratch() or view.settings().get('is_widget'): return
        vid = view.id()
        if not G_REGISTER.has_key(vid): G_REGISTER[vid] = PosStorage(view)
        G = G_REGISTER[vid]
        # reset current index
        G.curr_idx = 0
        # update saved postions
        self.update_pos(view)
        # insert current position
        self.insert_curr_pos(view)
        # print G.saved_pos


    def on_post_save(self, view):
        vid = view.id()
        vname = view.file_name()
        if G_REGISTER.has_key(vid):
            settings = sublime.load_settings('%s.sublime-settings' % __name__)
            settings.set(vname, ",".join(map(str, G_REGISTER[vid].saved_pos)))
            sublime.save_settings('%s.sublime-settings' % __name__)

    def on_close(self, view):
        vid = view.id()
        if G_REGISTER.has_key(vid): G_REGISTER.pop(vid)