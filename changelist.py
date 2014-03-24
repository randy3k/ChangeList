import sublime, sublime_plugin
import os
import sys
import json
import codecs
try:
    from .jsonio import JsonIO
except:
    from jsonio import JsonIO

is_ST2 = int(sublime.version()) < 3000

key_prefix = "cl"
CLjson = os.path.join(sublime.packages_path(), 'User', 'ChangeList.json')

# Change List object
class CList():
    LIST_LIMIT = 50
    key_counter = 0
    pointer = -1
    key_list = []
    dictionary = {}

    @classmethod
    def get_clist(cls, view):
        vid = view.id()
        vname = view.file_name()
        if vid in cls.dictionary:
            this_clist = cls.dictionary[vid]
        else:
            this_clist = CList(view)
            cls.dictionary[vid] = this_clist
            jfile = JsonIO(CLjson)
            data = jfile.load(default={})
            f = lambda s: sublime.Region(int(s[0]),int(s[1])) if len(s)==2 else sublime.Region(int(s[0]),int(s[0]))
            try:
                if vname in data:
                    print("Reloading keys...")
                    sel_list = [[f(s.split(",")) for s in sel.split(":")] for sel in data[vname]['history'].split("|")]
                    this_clist.reload_keys(sel_list)
            except:
                print("Reload keys failed!")
        return this_clist

    def __init__(self, view):
        self.view = view

    def push_key(self):
        view = self.view
        region_list = list(view.sel())
        if not region_list: return

        if self.key_list:
            last_sel = view.get_regions(self.key_list[-1])
            # dont push key if no jump
            if last_sel == region_list: return

            # delete last key if same line
            if len(last_sel) == len(region_list):
                if all([view.rowcol(i.begin())[0]==view.rowcol(j.begin())[0] for i,j in zip(last_sel, region_list)]):
                    self.key_counter -= 1
                    self.key_list.pop(-1)

        self.pointer = -1
        key = self.generate_key()
        view.erase_regions(key)
        view.add_regions(key, region_list ,"")
        self.key_list.append(key)

    def generate_key(self):
        self.key_counter += 1
        self.key_counter %= self.LIST_LIMIT * 2

        # if number of keys doubles the LIST_LIMIT, reload the keys
        if self.key_counter == 0:
            self.reload_keys()
            self.key_counter += 1
        return key_prefix+str(self.key_counter)

    def reload_keys(self, sel_list=None):
        view = self.view
        if not sel_list: sel_list = [self.view.get_regions(key) for key in self.key_list]
        for i,sel in enumerate(sel_list):
            view.erase_regions(key_prefix+str(i+1))
            view.add_regions(key_prefix+str(i+1), sel, "")
        self.key_list = [key_prefix+str(i+1) for i in range(len(sel_list))]
        self.key_counter = len(sel_list)


    def trim_keys(self):
        view = self.view
        if len(self.key_list) > self.LIST_LIMIT:
            for i in range(0, len(self.key_list) - self.LIST_LIMIT):
                key = self.key_list[i]
                view.erase_regions(key)
            del self.key_list[: len(self.key_list) - self.LIST_LIMIT]

    def remove_empty_keys(self):
        view = self.view
        new_key_list = []
        for key in self.key_list:
            # print(view.get_regions(key))
            if view.get_regions(key):
                new_key_list.append(key)
            else:
                view.erase_regions(key)
        self.key_list = new_key_list

    def goto(self, index):
        # print(self.key_list)
        view = self.view
        if index>=0 or index< -len(self.key_list): return
        self.pointer = index
        sel = view.get_regions(self.key_list[index])
        view.sel().clear()
        for s in sel:
            view.sel().add(s)
        view.set_viewport_position((view.viewport_position()[0], 0))
        row, col = view.rowcol(view.sel()[-1].end())
        view.show(view.text_point(row+5,col), False)
        # to reactivate cursor
        view.run_command("move", {"by": "characters", "forward" : False})
        view.run_command("move", {"by": "characters", "forward" : True})


class CListener(sublime_plugin.EventListener):
    def on_modified(self, view):
        if view.is_scratch() or view.settings().get('is_widget'): return
        this_clist = CList.get_clist(view)
        this_clist.remove_empty_keys()
        this_clist.push_key()
        this_clist.trim_keys()

    def on_post_save(self, view):
        this_clist = CList.get_clist(view)
        vname = view.file_name()
        jfile = JsonIO(CLjson)
        data = jfile.load(default={})
        f = lambda s: str(s.begin())+","+str(s.end()) if s.begin()!=s.end() else str(s.begin())
        data[vname] =  {"history": "|".join([":".join([f(s) for s in view.get_regions(key)]) for key in this_clist.key_list])}
        jfile.save(data, indent=0)

    def on_close(self, view):
        vid = view.id()
        if vid in CList.dictionary: CList.dictionary.pop(vid)


class JumpToChange(sublime_plugin.TextCommand):
    def run(self, _, **kwargs):
        view = self.view

        if view.is_scratch() or view.settings().get('is_widget'): return
        this_clist = CList.get_clist(view)
        if not this_clist.key_list: return
        if 'move' in kwargs:
            move = kwargs['move']
            if move == -1 and this_clist.pointer == -1 and view.get_regions(this_clist.key_list[-1]) != list(view.sel()):
                move = 0
            index = this_clist.pointer+move
        elif 'index' in kwargs:
            index = kwargs['index']
        else:
            return
        if index>=0 or index< -len(this_clist.key_list): return
        this_clist.goto(index)
        sublime.status_message("@[%s]" % str(-index-1))

class ShowChangeList(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if view.is_scratch() or view.settings().get('is_widget'): return
        this_clist = CList.get_clist(view)
        if not this_clist.key_list: return
        def f(i,key):
            begin = view.get_regions(key)[0].begin()
            return "%3d: %s" % (view.rowcol(begin)[0]+1, view.substr(view.line(begin)).strip())
        display_list = [ f(i,key) for i,key in enumerate(reversed(this_clist.key_list))]
        self.savept = [s for s in view.sel()]
        if is_ST2:
            self.window.show_quick_panel(display_list, self.on_done, sublime.MONOSPACE_FONT)
        else:
            self.window.show_quick_panel(display_list, self.on_done, sublime.MONOSPACE_FONT, on_highlight=self.on_done)

    def on_done(self, action):
        view = self.window.active_view()
        if action==-1: 
            view.sel().clear()
            for s in self.savept: view.sel().add(s)
            return
        view.run_command("jump_to_change", {"index" : -action-1})


class MaintainChangeList(sublime_plugin.WindowCommand):

    def show_quick_panel(self, options, done):
        sublime.set_timeout(lambda: self.window.show_quick_panel(options, done), 10)

    def run(self):
        view = self.window.active_view()
        if view.is_scratch() or view.settings().get('is_widget'): return
        try:
            fname = os.path.basename(view.file_name())
        except:
            fname = "untitled"
        self.show_quick_panel(["Rebuild History", "Clear History - "+fname, "Clear All History"], self.confirm)

    def confirm(self, action):
        if action<0: return
        self.action = action
        self.show_quick_panel(["Cancel", "Apply"], self.on_done)

    def on_done(self, confirm):
        view = self.window.active_view()
        if confirm<=0:
            self.run()
            return

        action = self.action
        jfile = JsonIO(CLjson)
        if action==0:
            data = jfile.load(default={})
            for item in [item for item in data if not os.path.exists(item)]:
                data.pop(item)
            jfile.save(data, indent=0)
            sublime.status_message("Change List History is rebuilt successfully.")
        elif action==1:
            vid = view.id()
            vname = view.file_name()
            if vid in CList.dictionary: CList.dictionary.pop(vid)
            if vname:
                data = load_jsonfile()
                if vname in data:
                    data.pop(vname)
                    jfile.save(data, indent=0)
            sublime.status_message("Change List (this file) is cleared successfully.")
        elif action==2:
            CList.dictionary = {}
            jfile.remove()
            sublime.status_message("Change List (all file) is cleared successfully.")
