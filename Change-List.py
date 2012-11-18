import sublime, sublime_plugin

if not 'EDTLOC' in globals(): EDTLOC = {} # to store edited locations
if not 'FILENOL' in globals(): FILENOL = {} # to store num of lines
if not 'CURINX' in globals(): CURINX = {} # to store current location index

class PreviousChangeCommand(sublime_plugin.TextCommand):
	def run(self,_):
		view = self.view
		vid = view.id()
		if not EDTLOC.has_key(vid): return
		if not EDTLOC[vid][(CURINX[vid]+1):]: return
		pos = EDTLOC[vid][CURINX[vid]+1]
		region = view.text_point(pos[0],pos[1])
		view.sel().clear()
		view.show(region)
		view.sel().add(region)
		CURINX[vid] = CURINX[vid]+1
		msg = "@Change List [" + str(CURINX[vid]) + "]"
		sublime.status_message(msg)


class NextChangeCommand(sublime_plugin.TextCommand):
	def run(self,_):
		view = self.view
		vid = view.id()
		if not EDTLOC.has_key(vid): return
		if CURINX[vid]==0: return
		pos = EDTLOC[vid][CURINX[vid]-1]
		region = view.text_point(pos[0],pos[1])
		view.sel().clear()
		view.show(region)
		view.sel().add(region)
		CURINX[vid] = CURINX[vid]-1
		msg = "@Change List [" + str(CURINX[vid]) + "]"
		sublime.status_message(msg)

class ChangeList(sublime_plugin.EventListener):
	def on_load(self, view):
		vid = view.id()
		vname = view.file_name()		
		settings = sublime.load_settings('%s.sublime-settings' % __name__)
		EDTLOC[vid] = [map(int, item.split(",")) for item in settings.get(vname).split("|")]
		CURINX[vid] = 0

	def on_modified(self, view):
		vid = view.id()
		curr_row, curr_col = view.rowcol(view.sel()[0].end())
		# current num of lines
		filenol = view.rowcol(view.size())[0]

		if not EDTLOC.has_key(vid):
			EDTLOC[vid] = []
		if not FILENOL.has_key(vid):
			FILENOL[vid] = filenol
		CURINX[vid] = 0

		if EDTLOC[vid]:
			# if num of lines changes
			if FILENOL[vid] != filenol:
				print(filenol)
				# change in num of lines
				delta = filenol-FILENOL[vid]
				# change rows that is after the current line
				EDTLOC[vid] = map(lambda pos: [pos[0]+delta*(pos[0] >= curr_row), pos[1]], EDTLOC[vid])
				# drop position if position is invalid
				EDTLOC[vid] = filter(lambda pos: (pos[0]>=0) & (pos[0]<=filenol), EDTLOC[vid])
				# update num of lines
				FILENOL[vid] = filenol		
			
			if abs(EDTLOC[vid][0][0] - curr_row)>1:
				EDTLOC[vid].insert(0,[int(curr_row), int(curr_col)])
			else:
				EDTLOC[vid][0] = [int(curr_row), int(curr_col)]	
		else:
			EDTLOC[vid] = [[int(curr_row), int(curr_col)]]

		if len(EDTLOC[vid])>50:
			EDTLOC[vid].pop()
		print(EDTLOC[vid])

	def on_post_save(self, view):
		vid = view.id()
		vname = view.file_name()		
		settings = sublime.load_settings('%s.sublime-settings' % __name__)
		settings.set(vname, "|".join([",".join(map(str, item)) for item in EDTLOC[vid]]))	
		sublime.save_settings('%s.sublime-settings' % __name__)

	def on_close(self, view):
		vid = view.id()	
		EDTLOC.pop(vid)
		FILENOL.pop(vid)
		CURINX.pop(vid)