Changes List for Sublime Text 2
====================

Introduction
------------
	This plugin is to recover the full functionality of Changes-List of VI.
	There are a few LastEdit plugins . For examples:
	https://github.com/SamPeng87/sublime-last-edit
	https://github.com/khrizt/GotoLastEdit
	https://github.com/abrookins/GotoLastEdit

	However, they do not keep editing history after the file is closed.


Keymap
-----------------------
		[
		  { "keys": ["super+;"], "command": "previous_change"},
		  { "keys": ["super+,"], "command": "next_change"},
		  {	"keys": ["g",";"], "command": "previous_change",
		  	"context": [{"key": "setting.command_mode"}]},
		  {	"keys": ["g",","], "command": "next_change",
		  	"context": [{"key": "setting.command_mode"}]}
		]
