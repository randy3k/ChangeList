import sublime, sublime_plugin
import re

CHGPOS = {}
LASTLINE = {}
CURINX = {}

class PreviousChangeCommand(sublime_plugin.TextCommand):
	def run(self,_):
		view = self.view
		vid = view.id()
		if not CHGPOS.has_key(vid): return
		if not CHGPOS[vid][(CURINX[vid]+1):]: return
		pos = CHGPOS[vid][CURINX[vid]+1]
		region = view.text_point(pos[0],pos[1])
		view.sel().clear()
		view.show(region)
		view.sel().add(region)
		CURINX[vid] = CURINX[vid]+1

class NextChangeCommand(sublime_plugin.TextCommand):
	def run(self,_):
		view = self.view
		vid = view.id()
		if not CHGPOS.has_key(vid): return
		if CURINX[vid]==0: return
		pos = CHGPOS[vid][CURINX[vid]-1]
		region = view.text_point(pos[0],pos[1])
		view.sel().clear()
		view.show(region)
		view.sel().add(region)
		CURINX[vid] = CURINX[vid]-1

class ChangeList(sublime_plugin.EventListener):
	def on_load(self, view):
		print("initialize")
		vid = view.id()
		vname = view.file_name()		
		settings = sublime.load_settings('%s.sublime-settings' % __name__)
		CHGPOS[vid] = [map(int, item.split(",")) for item in settings.get(vname).split("|")]
		CURINX[vid] = 0
		print(CHGPOS)

	def on_modified(self, view):
		vid = view.id()
		sel = view.sel()[0]
		currA = sel.begin()
		currB = sel.end()
		curr_line, curr_col = view.rowcol(currB)

		if not CHGPOS.has_key(vid):
			CHGPOS[vid] = []
		if not LASTLINE.has_key(vid):
			LASTLINE[vid] = view.rowcol(view.size())[0]
		CURINX[vid] = 0

		if CHGPOS[vid]:
			if LASTLINE[vid] != view.rowcol(view.size())[0]:
				delta = view.rowcol(view.size())[0]-LASTLINE[vid]
				for i,pos in enumerate(CHGPOS[vid]):
					if pos[0] >= curr_line:
							CHGPOS[vid][i] = [pos[0]+delta, pos[1]]
				# drop the position if the line is deleted
				CHGPOS[vid] = filter(lambda pos: pos[0]>=0, CHGPOS[vid])
				# update the length of file
				LASTLINE[vid] = view.rowcol(view.size())[0]		
			
			if abs(CHGPOS[vid][0][0] - curr_line)>1:
				CHGPOS[vid].insert(0,[int(curr_line), int(curr_col)])
			else:
				CHGPOS[vid][0] = [int(curr_line), int(curr_col)]	
		else:
			CHGPOS[vid] = [[int(curr_line), int(curr_col)]]

		if len(CHGPOS[vid])>20:
			CHGPOS[vid].pop()
		print(CHGPOS)

	def on_post_save(self, view):
		vid = view.id()
		vname = view.file_name()		
		settings = sublime.load_settings('%s.sublime-settings' % __name__)
		settings.set(vname, "|".join([",".join(map(str, item)) for item in CHGPOS[vid]]))	
		sublime.save_settings('%s.sublime-settings' % __name__)

	def on_close(self, view):
		vid = view.id()	
		CHGPOS.pop(vid)
		LASTLINE.pop(vid)
		CURINX.pop(vid)