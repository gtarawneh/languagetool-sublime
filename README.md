#### Brief Summary

This is a simple adapter to integrate [LanguageTool](https://languagetool.org/) (an open source proof-reading program) into Sublime Text 2/3.

From https://www.languagetool.org/:

> LanguageTool is an Open Source proof­reading program for English, French, German, Polish, and more than 20 other languages. It finds many errors that a simple spell checker cannot detect and several grammar problems.

![](https://cdn.rawgit.com/gtarawneh/languagetool-sublime/master/demo.gif)

#### Installation

If you're using Package Control then open the Command Palette (`Ctrl+Shift+p`), type `install`, press Enter then type `languagetool` and press Enter again. Otherwise you can install manually by going to your packages directory (`Ctrl+Shift+p`, type `browse` and press Enter) and cloning the repo there.

#### Usage

Open the file you want to proof-read then:

1. Run a language check (`Ctrl+Shift+c`). Any problems identified by LanguageTool will be highlighted.
2. Move focus between the problems using `Alt+Down` (next) and `Alt+Up` (previous).
3. A panel at the bottom will display a brief description  of the highlighted problem and suggest corrections if available.
4. Begin typing to correct a selected problem or press `Alt+f` to apply the suggested correction.
5. To ignore the selected problem, press `Alt+d`.
6. Auto-correcting a problem (`Alt+f`) or ignoring it (`Alt+d`) will automatically move focus to the next problem.

All plugin commands and their keyboard shortcuts can be listed in the command palette by typing `LanguageTool:`.

#### Server Configuration

The adapter sends the text to be checked to a LanguageTool server via http. The server is initially configured (in the file `LanguageTool.sublime-settings`) as `https://languagetool.org:8081/`. This is just to get the adapter up and running after installation and should not be kept for continuous use. Please download LanguageTool then run and configure the adapter to use [your own LanguageTool server](http://wiki.languagetool.org/http-server).

#### Contributing

Feel free to fork and improve. I tried to keep things neat and tidy but I've never coded in python and have little experience with sublime so please forgive any coding idiosyncrasies.
