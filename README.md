The missing Change List for Sublime Text 2/3 - History List, Last Edit ...
====================
It remembers where changes were made.
<img src="https://github.com/randy3k/ChangeList/raw/master/changelist.png">

Installation
------------
1. Via [Package Control](http://wbond.net/sublime_packages/package_control)

2. Change key bindings, ignore this if you want to stay with the original keys. The User Key Bindings file can be accessed from Preferences -> Key Bindings - User.

        [
            { "keys": ["ctrl+;"], "command": "jump_to_change", "args": {"move": -1}},
            { "keys": ["ctrl+,"], "command": "jump_to_change", "args": {"move": 1}},
            { "keys": ["ctrl+."], "command": "jump_to_change", "args": {"index": -1}}
        ]

Usage
------------

* Launch ``Change List: Show`` in Command Palette to show Change List.
* Launch ``Change List: Maintenance`` in Command Palette to maintain Change List.
* ``ctrl+;``  go to previous edited location
* ``ctrl+,``  go to next edited location
* ``ctrl+.``  go to the last edited location

Others
-----------
This plugin aims at recovering the full functionality of change list of VIM.<BR>
Last 50 history for each file is saved.<BR>
This plugin saves history to ``Packages/User/ChangeList.json``.<BR>

