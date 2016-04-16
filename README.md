#### Brief Summary

This is a simple adapter to integrate [LanguageTool](https://languagetool.org/) (an open source proof-reading program) into [Sublime Text](https://www.sublimetext.com/). It is compatible with both ST2 and ST3.

#### How to Install

Go to your Sublime Text packages directory and execute `git clone git://github.com/gtarawneh/languagetool-sublime.git`. The plugin will become available for use instantly.

To find your packages directory open-up the console (click `View` then `Show Console` from the menu) and execute `sublime.packages_path()`.

#### How to Use

Open the (plain text) file you want LanguageTool to proof-read then:

1. Run a language check (`Ctrl+Shift+c`). Any problems identified by LanguageTool will be highlighted.
2. Move focus between the problems using `Alt+Down` (next) and `Alt+Up` (previous).
3. Each time a problem is in focus, the status bar will display a description of the problem and (if available) suggested corrections between brackets.
4. Begin typing to correct a selected problem or press `Alt+f` to apply suggested corrections if available.
5. To ignore the selected problem, press `Alt+d`.
6. Auto-correcting a problem (`Alt+f`) or ignoring it (`Alt+d`) will automatically move focus to the next problem.

All plugin commands and their keyboard shortcuts can be listed in the command palette by typing `LanguageTool:`.

#### Configuration

The adapter sends the text to be checked to a LanguageTool server via http. The server is initially configured (in the file `LanguageTool.sublime-settings`) as `https://languagetool.org:8081/`. This is just to get the adapter up and running after installation and should not be kept for continuous use. Please download LanguageTool then run and configure the adapter to use [your own LanguageTool server](http://wiki.languagetool.org/http-server).

#### Contributing

Feel free to fork and improve. I tried to keep things neat and tidy but I've never coded in python and have little experience with sublime so please forgive any coding idiosyncrasies.