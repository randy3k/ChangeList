import sublime, sublime_plugin

# to store edited locations
if not 'EDTLOC' in globals(): EDTLOC = {}
# to store num of lines
if not 'FILENOL' in globals(): FILENOL = {}
# to store current location index
if not 'CURINX' in globals(): CURINX = {}
# to store current location index
if not 'SLTDLINE' in globals(): SLTDLINE = {}

class JumpToChangeCommand(sublime_plugin.TextCommand):
	def run(self, _, move):
		view = self.view
		vid = view.id()
		curr_row = view.rowcol(view.sel()[0].end())[0]
		if (not EDTLOC.has_key(vid)) | (not EDTLOC[vid]): return
		RECINX = len(EDTLOC[vid])-1
		# if the cursor has moved away from the recent edited location, set move = 0
		if (CURINX[vid]==RECINX) & (move==-1) & (curr_row != EDTLOC[vid][RECINX][0]): move = 0
		NEWINX = CURINX[vid]+move
		if (NEWINX<0)| (NEWINX>RECINX): return
		pos = EDTLOC[vid][NEWINX]
		region = view.text_point(pos[0],pos[1])
		view.sel().clear()
		view.show(region)
		view.sel().add(region)
		CURINX[vid] = NEWINX
		msg = "@Change List [" + str(RECINX-CURINX[vid]) + "]"
		sublime.status_message(msg)

class ChangeList(sublime_plugin.EventListener):
	def on_load(self, view):
		vid = view.id()
		vname = view.file_name()
		# current num of lines
		filenol = view.rowcol(view.size())[0]		
		try:		
			settings = sublime.load_settings('%s.sublime-settings' % __name__)
			EDTLOC[vid] = [map(int, item.split(",")) for item in settings.get(vname).split("|")]
			CURINX[vid] = len(EDTLOC[vid])-1
		except:
			EDTLOC[vid] = []
			CURINX[vid] = 0
		FILENOL[vid] = filenol	

	# required for detecting deleted selections
	def on_selection_modified(self, view):
		vid = view.id()
		# get the current multi cursor locations
		SLTDLINE[vid] = map(lambda s: view.rowcol(s.end())[0] ,view.sel())

	def on_modified(self, view):
		vid = view.id()
		curr_row, curr_col = view.rowcol(view.sel()[0].end())
		# current num of lines
		filenol = view.rowcol(view.size())[0]
		sltdline = map(lambda s: view.rowcol(s.end())[0] ,view.sel())
		if not EDTLOC.has_key(vid): EDTLOC[vid] = []
		if not FILENOL.has_key(vid): FILENOL[vid] = filenol

		if EDTLOC[vid]:
			# if num of lines changes
			if FILENOL[vid] != filenol:
				deltas = map(lambda x,y: x-y, sltdline, SLTDLINE[vid])
				deltas = [deltas[0]]+[x - deltas[i - 1] for i, x in enumerate(deltas) if i>0]
				print(deltas)
				for i, delta in enumerate(deltas):
					# drop pos
					if delta<0:
						EDTLOC[vid] = \
							filter(lambda pos: (pos[0]<=sltdline[i]) | (pos[0]>SLTDLINE[vid][i]), EDTLOC[vid])
					# update pos that is after the current line
					EDTLOC[vid] = \
						map(lambda pos: [pos[0]+delta*(pos[0] >= max(SLTDLINE[vid][i],sltdline[i])), pos[1]], EDTLOC[vid])
						
				# drop position if position is invalid
				EDTLOC[vid] = filter(lambda pos: (pos[0]>=0) & (pos[0]<=filenol), EDTLOC[vid])
				# update num of lines
				FILENOL[vid] = filenol		
			
			RECINX = len(EDTLOC[vid])-1
			if abs(EDTLOC[vid][RECINX][0] - curr_row)>1:
				EDTLOC[vid].append([int(curr_row), int(curr_col)])
			else:
				EDTLOC[vid][RECINX] = [int(curr_row), int(curr_col)]	
		else:
			EDTLOC[vid] = [[int(curr_row), int(curr_col)]]

		if len(EDTLOC[vid])>50:
			EDTLOC[vid].pop(0)
		CURINX[vid] = len(EDTLOC[vid])-1			
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