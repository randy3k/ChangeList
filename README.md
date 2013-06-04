The missing Change List for Sublime Text 2/3 - History List, Last Edit ...
====================
It remembers where changes were made.
<img src="https://github.com/randy3k/ChangeList/raw/master/changelist.png">

Installation
------------
1. Via [Package Control](http://wbond.net/sublime_packages/package_control)

2. Install keymap

        [
            { "keys": ["ctrl+;"], "command": "jump_to_change", "args": {"move": 1}},
            { "keys": ["ctrl+,"], "command": "jump_to_change", "args": {"move": -1}},
            { "keys": ["ctrl+."], "command": "jump_to_change", "args": {"index": 0}}
        ]
[Vintage](https://github.com/sublimehq/Vintage)

        [
            { "keys": ["g",";"], "command": "jump_to_change", "args": {"move": 1}, "context": [{"key": "setting.command_mode"}]},
            { "keys": ["g",","], "command": "jump_to_change", "args": {"move": -1}, "context": [{"key": "setting.command_mode"}]},
            { "keys": ["g","."], "command": "jump_to_change", "args": {"index": -1}, "context": [{"key": "setting.command_mode"}]}
        ]
[Vintageous](https://github.com/guillermooo/Vintageous?source=c)

        [
            { "keys": ["g",";"], "command": "jump_to_change", "args": {"move": 1}, "context": [{"key": "setting.command_mode"}]},
            { "keys": ["g",","], "command": "jump_to_change", "args": {"move": -1}, "context": [{"key": "setting.command_mode"}]},
            { "keys": ["g","."], "command": "jump_to_change", "args": {"index": -1}, "context": [{"key": "setting.command_mode"}]}
        ]


Introduction
------------

This plugin aims at recovering the full functionality of change list of VIM.
* Launch ``Change List: Show`` in Command Palette to show Change List.
* Launch ``Change List: Manage`` in Command Palette to manage Change List.
* ``ctrl+;``  go to previous edited location
* ``ctrl+,``  go to next edited location
* ``ctrl+.``  go to the last edited location

Last 50 history for each file is saved.<BR>
This plugin saves history to ``Packages/User/ChangeList.json``.<BR>

