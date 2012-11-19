import sublime, sublime_plugin
import os

# to store edited locations
if not 'EPOS' in globals(): EPOS = {}
# to store num of lines
if not 'FILENOL' in globals(): FILENOL = {}
# to store current index
if not 'CURIDX' in globals(): CURIDX = {}
if not 'SELROW' in globals(): SELROW = {}

class JumpToChangeCommand(sublime_plugin.TextCommand):
	def run(self, _, move):
		view = self.view
		vid = view.id()
		curr_row = view.rowcol(view.sel()[0].end())[0]
		if not EPOS.has_key(vid): return
		if not EPOS[vid]: return
		RECIDX = len(EPOS[vid])-1
		# if the cursor has moved away from the recent edited location, set move = 0
		if (CURIDX[vid]==RECIDX) & (move==-1) & (curr_row != EPOS[vid][RECIDX][0]): move = 0
		NEWIDX = CURIDX[vid]+move
		if (NEWIDX<0)| (NEWIDX>RECIDX): return
		pos = EPOS[vid][NEWIDX]
		region = view.text_point(pos[0],pos[1])
		view.sel().clear()
		view.show(region)
		view.sel().add(region)
		CURIDX[vid] = NEWIDX
		msg = "@Change List [" + str(RECIDX-CURIDX[vid]) + "]"
		sublime.status_message(msg)

class ClearChangeList(sublime_plugin.WindowCommand):
	def run(self):
		self.view = self.window.active_view()
		try:
			fname = os.path.basename(self.view.file_name())
		except:
			fname = "New file"
		self.window.show_quick_panel(["This file - " + fname, "All file"], self.on_done)
	
	def on_done(self, action):	
		global EPOS
		if action==0:
			vid = self.view.id()				
			settings = sublime.load_settings('%s.sublime-settings' % __name__)	
			try:
				vname = self.view.file_name()
				if settings.has(vname): settings.erase(vname)	
			except:
				True
			sublime.save_settings('%s.sublime-settings' % __name__)
			sublime.status_message("Clear Change List (this file) successfually.")
	  		if EPOS.has_key(vid): EPOS[vid] = []
	  	else:
	  		try:
	  			path = sublime.packages_path() + "/User/" + '%s.sublime-settings' % __name__
	  			if os.path.exists(path): os.remove(path)
	  		except (OSError, IOError):
	  			sublime.error_message("Error occurred while clearing Change List!")
	  			return False
    		sublime.status_message("Clear Change List (all file) successfually.")
    		EPOS  = {}


class ChangeListener(sublime_plugin.EventListener):

	def on_load(self, view):
		vid = view.id()
		vname = view.file_name()
		settings = sublime.load_settings('%s.sublime-settings' % __name__)
		if settings.has(vname):
			EPOS[vid] = [map(int, item.split(",")) for item in settings.get(vname).split("|")]
		else:
			EPOS[vid] = []
		CURIDX[vid] = len(EPOS[vid])-1

	# required for detecting deleted selections
	def on_selection_modified(self, view):
		vid = view.id()
		# get the current multi cursor locations
		SELROW[vid] = map(lambda s: int(view.rowcol(s.end())[0]) ,view.sel())

	def on_modified(self, view):
		if view.is_scratch() or view.settings().get('is_widget'): return
		vid = view.id()
		curr_pos = map(lambda s: map(int, view.rowcol(s.end())) ,view.sel())
		# current num of lines
		file_nol = view.rowcol(view.size())[0]

		if EPOS[vid]:
			# if num of lines changes
			if not FILENOL.has_key(vid): FILENOL[vid] = file_nol
			if FILENOL[vid] != file_nol:
				deltas = map(lambda x,y: x[0]-y, curr_pos, SELROW[vid])
				deltas = [int(x - deltas[i-1]) for i,x in enumerate(deltas) if i>0]
				deltas = [int(file_nol-FILENOL[vid]-sum(deltas))] + deltas
				# print(deltas)
				for i, delta in enumerate(deltas):
					# drop pos
					if (delta<0):
							EPOS[vid] = \
								filter(lambda pos: (pos[0]<curr_pos[i][0]) | (pos[0]>SELROW[vid][i]), EPOS[vid])
					# update pos that is afterwards				
					EPOS[vid] = \
						map(lambda pos: [pos[0]+delta*(pos[0] > SELROW[vid][i]), pos[1]], EPOS[vid])
					SELROW[vid] = \
						map(lambda row: row+delta*(row > SELROW[vid][i]) , SELROW[vid])							
						
				# drop position if position is invalid
				EPOS[vid] = filter(lambda pos: (pos[0]>=0) & (pos[0]<=file_nol), EPOS[vid])
				# update num of lines
				FILENOL[vid] = file_nol

		if EPOS[vid]:
			RECIDX = len(EPOS[vid])-1
			if abs(EPOS[vid][RECIDX][0] - curr_pos[0][0])>1:
				EPOS[vid].append(curr_pos[0])
			else:
				EPOS[vid][RECIDX] = curr_pos[0]	

			if len(EPOS[vid])>50: EPOS[vid].pop(0)
		else:
			EPOS[vid] = [curr_pos[0]]

		CURIDX[vid] = len(EPOS[vid])-1
		print(map(lambda x: [x[0]+1,x[1]+1], EPOS[vid]))


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
		if CURIDX.has_key(vid): CURIDX.pop(vid)
		if SELROW.has_key(vid): SELROW.pop(vid)