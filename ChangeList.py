import sublime, sublime_plugin
import os
import sys
import json
import codecs

# clist_dict = {}
if not 'clist_dict' in globals(): clist_dict = {}

# Change List object
class CList():
    LIST_LIMIT = 50
    key_counter = 0
    pointer = -1
    key_list = []

    def __init__(self, view):
        self.view = view

    def push_key(self):
        view = self.view
        region_list = list(view.sel())
        if not region_list: return

        if self.key_list:
            last_sel = view.get_regions(self.key_list[-1])
            if last_sel == region_list: return
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
        return str(self.key_counter)

    def reload_keys(self, sel_list=None):
        view = self.view
        if not sel_list: sel_list = [self.view.get_regions(key) for key in self.key_list]
        for i,sel in enumerate(sel_list):
            view.erase_regions(str(i+1))
            view.add_regions(str(i+1), sel, "")
        self.key_list = [str(s) for s in range(len(sel_list)+1)[1:]]
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
        view = self.view
        if index>=0 or index< -len(self.key_list): return
        self.pointer = index
        sel = view.get_regions(self.key_list[index])
        view.sel().clear()
        view.show(sel[0], True)
        for s in sel:
            view.sel().add(s)

def load_jsonfile():
    jsonFilepath = os.path.join(sublime.packages_path(), 'User', 'ChangeList.json')
    if os.path.exists(jsonFilepath):
        jsonFile = codecs.open(jsonFilepath, "r+", encoding="utf-8")
        try:
            data = json.load(jsonFile)
        except:
            data = {}
        jsonFile.close()
    else:
        jsonFile = codecs.open(jsonFilepath, "w+", encoding="utf-8")
        data = {}
        jsonFile.close()
    return data

def save_jsonfile(data):
    jsonFilepath = os.path.join(sublime.packages_path(), 'User', 'ChangeList.json')
    jsonFile = codecs.open(jsonFilepath, "w+", encoding="utf-8")
    jsonFile.write(json.dumps(data, ensure_ascii=False))
    jsonFile.close()

def remove_jsonfile():
    jsonFilepath = os.path.join(sublime.packages_path(), 'User', 'ChangeList.json')
    if os.path.exists(jsonFilepath): os.remove(jsonFilepath)

def get_clist(view):
    global clist_dict
    vid = view.id()
    vname = view.file_name()
    if vid in clist_dict:
        this_clist = clist_dict[vid]
    else:
        this_clist = CList(view)
        clist_dict[vid] = this_clist
        data = load_jsonfile()
        f = lambda s: sublime.Region(int(s[0]),int(s[1])) if len(s)==2 else sublime.Region(int(s[0]),int(s[0]))
        if vname in data:
            sel_list = [[f(s.split(",")) for s in sel.split(":")] for sel in data[vname]['history'].split("|")]
            this_clist.reload_keys(sel_list)
    return this_clist

class CListener(sublime_plugin.EventListener):
    def on_modified(self, view):
        if view.is_scratch() or view.settings().get('is_widget'): return
        this_clist = get_clist(view)
        this_clist.remove_empty_keys()
        this_clist.push_key()
        this_clist.trim_keys()
        # print(this_clist, this_clist.key_list)
        # for key in this_clist.key_list:
        #     print(view.get_regions(key))

    def on_post_save(self, view):
        this_clist = get_clist(view)
        vname = view.file_name()
        data = load_jsonfile()
        f = lambda s: str(s.begin())+","+str(s.end()) if s.begin()!=s.end() else str(s.begin())
        data[vname] =  {"history": "|".join([":".join([f(s) for s in view.get_regions(key)]) for key in this_clist.key_list])}
        save_jsonfile(data)

    def on_close(self, view):
        vid = view.id()
        if vid in clist_dict: clist_dict.pop(vid)


class JumpToChange(sublime_plugin.TextCommand):
    def run(self, _, **kwargs):
        view = self.view
        # reset vintageous action
        try:
            vintage = view.settings().get('vintage')
            vintage['action'] = None
            view.settings().set('vintage', vintage)
        except:
            pass

        if view.is_scratch() or view.settings().get('is_widget'): return
        this_clist = get_clist(view)
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
        # print(len(this_clist.key_list))
        this_clist.goto(index)
        # to reactivate cursor
        view.run_command("move", {"by": "characters", "forward" : False})
        view.run_command("move", {"by": "characters", "forward" : True})
        sublime.status_message("@[%s]" % str(-index-1))

class ShowChangeList(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if view.is_scratch() or view.settings().get('is_widget'): return
        this_clist = get_clist(view)
        if not this_clist.key_list: return
        def f(i,key):
            begin = view.get_regions(key)[0].begin()
            return "[%2d] %3d: %s" % (i, view.rowcol(begin)[0]+1, view.substr(view.line(begin)))
        self.window.show_quick_panel([ f(i,key)
                    for i,key in enumerate(reversed(this_clist.key_list))], self.on_done)

    def on_done(self, action):
        view = self.window.active_view()
        this_clist = get_clist(view)
        if action==-1: return
        # print(-action-1)
        view.run_command("jump_to_change", {"index" : -action-1})

class MaintainChangeList(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if view.is_scratch() or view.settings().get('is_widget'): return
        try:
            fname = os.path.basename(view.file_name())
        except:
            fname = "untitled"
        self.window.show_quick_panel(["Rebuild History", "Clear History - "+fname, "Clear All History"], self.on_done)

    def on_done(self, action):
        view = self.window.active_view()
        global clist_dict
        if action==0:
            data = load_jsonfile()
            for item in [item for item in data if not os.path.exists(item)]:
                data.pop(item)
            save_jsonfile(data)
            sublime.status_message("Change List History is rebuilt successfully.")
        elif action==1:
            vid = view.id()
            vname = view.file_name()
            if vid in clist_dict: clist_dict.pop(vid)
            if vname:
                data = load_jsonfile()
                if vname in data:
                    data.pop(vname)
                    save_jsonfile(data)
            sublime.status_message("Change List (this file) is cleared successfully.")
        elif action==2:
            clist_dict = {}
            remove_jsonfile()
            sublime.status_message("Change List (all file) is cleared successfully.")