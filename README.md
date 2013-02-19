Change List / History / Last Edit for Sublime Text 2
====================
It remembers where changes were made.
<img src="https://github.com/randy3k/ChangeList/raw/master/changelist.png">

Installation
------------
Via [Package Control](http://wbond.net/sublime_packages/package_control)
This is temporarily unavailable.

Introduction
------------

This plugin aims at recovering the full functionality of change list of VIM.
* Type ``Change List: Show`` in Command Palette to show Change List.
* Type ``Change List: Clear`` in Command Palette to clear Change List.
* ``super+;`` (Mac) or ``ctrl+;`` (Win/Linux) or ``g;`` (vintage command mode): go to previous edited location
* ``super+,`` or ``g,`` (vintage command mode): go to next edited location
* ``super+.`` or ``g.`` (vintage command mode): go to the last edited location

There are a few other "Last Edit" plugins . For examples:
* https://github.com/SamPeng87/sublime-last-edit
* https://github.com/khrizt/GotoLastEdit
* https://github.com/abrookins/GotoLastEdit
* https://github.com/Stuk/sublime-edit-history
* https://github.com/optilude/SublimeTextMisc/blob/master/navigationHistory.py
* https://gist.github.com/1993147

As far as I know, they do not keep history after the file is closed.<BR>
This plugin saves history to ``Packages/User/ChangeList.sublime-settings``.<BR>
For the moment, the last 50 history for each file will be saved.<BR>


Keymap
----------------------
It overwrites the default keymap ``super+,`` for consistency.<br>

Known issues
-----------------------
* Undo will update the change list. I have no idea on how to fix it at this moment.
* Multi cursor support is now limited, only the location of the first cursor will be saved.
  However, most multi cursor editing preserves history.
