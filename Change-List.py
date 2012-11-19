import sublime, sublime_plugin

# to store edited locations
if not 'EPOS' in globals(): EPOS = {}
# to store num of lines
if not 'FILENOL' in globals(): FILENOL = {}
# to store current index
if not 'CURINX' in globals(): CURINX = {}
if not 'SELROW' in globals(): SELROW = {}

class JumpToChangeCommand(sublime_plugin.TextCommand):
	def run(self, _, move):
		view = self.view
		vid = view.id()
		curr_row = view.rowcol(view.sel()[0].end())[0]
		if (not EPOS.has_key(vid)) | (not EPOS[vid]): return
		RECINX = len(EPOS[vid])-1
		# if the cursor has moved away from the recent edited location, set move = 0
		if (CURINX[vid]==RECINX) & (move==-1) & (curr_row != EPOS[vid][RECINX][0]): move = 0
		NEWINX = CURINX[vid]+move
		if (NEWINX<0)| (NEWINX>RECINX): return
		pos = EPOS[vid][NEWINX]
		region = view.text_point(pos[0],pos[1])
		view.sel().clear()
		view.show(region)
		view.sel().add(region)
		CURINX[vid] = NEWINX
		msg = "@Change List [" + str(RECINX-CURINX[vid]) + "]"
		sublime.status_message(msg)

class ChangeList(sublime_plugin.EventListener):

	def initialize(self,view):
		vid = view.id()
		vname = view.file_name()
		file_nol = view.rowcol(view.size())[0]			
		if not EPOS.has_key(vid): EPOS[vid] = []
		if not CURINX.has_key(vid): CURINX[vid] = 0		
		if not FILENOL.has_key(vid): FILENOL[vid] = file_nol	

	def on_load(self, view):
		vid = view.id()
		vname = view.file_name()
		# current num of lines
	
		try:		
			settings = sublime.load_settings('%s.sublime-settings' % __name__)
			EPOS[vid] = [map(int, item.split(",")) for item in settings.get(vname).split("|")]
			CURINX[vid] = len(EPOS[vid])-1
		finally:
			self.initialize(view)


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

		self.initialize(view)

		if EPOS[vid]:
			# if num of lines changes
			if FILENOL[vid] != file_nol:
				deltas = map(lambda x,y: x[0]-y, curr_pos, SELROW[vid])
				deltas = [int(x - deltas[i-1]) for i,x in enumerate(deltas) if i>0]
				deltas = [int(file_nol-FILENOL[vid]-sum(deltas))] + deltas
				print(deltas)
				for i, delta in enumerate(deltas):
					# drop pos
					if (delta<0) & (i==0):
							EPOS[vid] = \
								filter(lambda pos: (pos[0]<curr_pos[i][0]) | (pos[0]>SELROW[vid][i]), EPOS[vid])
					# update pos that is after the current line
					EPOS[vid] = \
						map(lambda pos: [pos[0]+delta*(pos[0] >= max(SELROW[vid][i],curr_pos[i][0])), pos[1]], EPOS[vid])
						
				# drop position if position is invalid
				EPOS[vid] = filter(lambda pos: (pos[0]>=0) & (pos[0]<=file_nol), EPOS[vid])
				# update num of lines
				FILENOL[vid] = file_nol		

		if EPOS[vid]:
			RECINX = len(EPOS[vid])-1
			if abs(EPOS[vid][RECINX][0] - curr_pos[0][0])>1:
				EPOS[vid].append(curr_pos[0])
			else:
				EPOS[vid][RECINX] = curr_pos[0]	

			if len(EPOS[vid])>50: EPOS[vid].pop(0)
		else:
			EPOS[vid] = [curr_pos[0]]

		CURINX[vid] = len(EPOS[vid])-1
		# print(EPOS[vid])


	def on_post_save(self, view):
		vid = view.id()
		vname = view.file_name()		
		settings = sublime.load_settings('%s.sublime-settings' % __name__)
		settings.set(vname, "|".join([",".join(map(str, item)) for item in EPOS[vid]]))	
		sublime.save_settings('%s.sublime-settings' % __name__)

	def on_close(self, view):
		vid = view.id()	
		EPOS.pop(vid)
		FILENOL.pop(vid)
		CURINX.pop(vid)