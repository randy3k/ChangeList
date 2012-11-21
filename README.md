Change List (Last Edit) for Sublime Text 2
====================
It remembers the locations where changes occurred.
<img src="https://github.com/randy3k/Change-List/raw/master/changelist.png">

Introduction
------------

This plugin aims at recovering the full functionality of change list of VIM.
* Type ``Change List: Show`` in Command Palette to show Change List.
* Type ``Change List: Clear`` in Command Palette to clear Change List.
* Type ``super+;`` or ``g;`` (vintage command mode) to go to previous edited location
* Type ``super+,`` or ``g,`` (vintage command mode) to go to next edited location
* Type ``super+.`` or ``g.`` (vintage command mode) to go to the last edited location

There are already a few other "LastEdit" plugins . For examples:
* https://github.com/SamPeng87/sublime-last-edit
* https://github.com/khrizt/GotoLastEdit
* https://github.com/abrookins/GotoLastEdit
* https://github.com/Stuk/sublime-edit-history
* https://github.com/optilude/SublimeTextMisc/blob/master/navigationHistory.py
* https://gist.github.com/1993147

However, they do not keep  history after the file is saved and closed (as far as I can tell).<BR>
This plugin saves history to ``Packages/User/Change-List.sublime-settings``.<BR>
For the moment, the last 50 editing history for each file will be saved.<BR>

Note: The cursor always stays in the same file, it does not jump between files.
I personally think that it is more useful than a jump list.

Keymap
----------------------
It overwrites the default keymap ``super+,`` for consistency.<br>
I wish to map <code>\`.</code> or ``'.`` to ``go to the last edited location``.
However vintage has used them for bookmarks and I couldn't overwrite them without touching vintage code.

Known issues
-----------------------
* Undo will change the history (ironic, huh!?). I have no idea on how to correct this at this moment.
* Multi cursor support is now limited, only the location of first cursor will be saved.
  However, multi cursor editing preserves the history.
