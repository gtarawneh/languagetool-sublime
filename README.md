<!-- ### LanguageTool - Sublime Adapter -->

#### Brief Summary

This is a simple adapter to add the functionality of [LanguageTool](https://languagetool.org/) (an open source proof-reading program) to [Sublime Text](https://www.sublimetext.com/).

#### How to Install

Go to your Sublime Text packages directory and execute `git clone git://github.com/gtarawneh/languagetool-sublime.git`. The plugin will become available for use instantly.

To find your packages directory open-up the console (click `View` then `Show Console` from the menu) and execute `sublime.packages_path()`.

#### How to Use

Open the (plain text) file you want LanguageTool to proof-read then:

1. Run a language check (`Ctrl+Shift+r`). Any problems identified by LanguageTool will be highlighted.
2. Move focus between the problems using `Alt+Down` (next) and `Alt+Up` (previous).
3. Each time a problem is in focus, the status bar will display a description of the problem and (if available) suggested corrections between brackets.
4. Begin typing to correct a selected problem or press `Alt+Right` to apply suggested corrections if available.
5. To ignore the selected problem, press `Alt+Left`.
6. Auto-correcting a problem (`Alt+Right`) or ignoring it (`Alt+Left`) will automatically move focus to the next problem.

All plugin commands and their keyboard shortcuts can be listed in the command palette by typing `LanguageTool:`.

#### Configuration

The adapter sends the text to be checked to a LanguageTool server via http. The server is initially configured (in the file `languagetool.sublime-settings`) as `https://languagetool.org:8081/`. This is just to get the adapter up and running after installation and should not be kept for continuous use. Please download LanguageTool then run and configure the adapter to use [your own LanguageTool server](http://wiki.languagetool.org/http-server).

#### Issues

The adapter is fully functional but has few nags which I'll try to address in the future:

* Re-running the language check will highlight all existing problems including any which have been previously ignored by the user (via `Alt+Left`)
* When a sentence is preceded by exactly 1 new line, problem highlights are offset by 1 character. This appears to be an issue with LanguageTool. If you notice any sentences where the highlights are off you can add one more (temporary) new lines before running language check as a walk-around solution.
* When running on tex or markdown files LanguageTool may incorrectly identify certain sequence like~this as typos.

#### Contributing

Feel free to fork and improve. I tried to keep things neat and tidy but I've never coded in python and have little experience with sublime so please forgive any coding idiosyncrasies. 