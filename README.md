#### Brief Summary

This is a simple adapter to integrate [LanguageTool](https://languagetool.org/) (an open source proof-reading program) into Sublime Text 2/3.

From https://www.languagetool.org/:

> LanguageTool is an Open Source proof­reading program for English, French, German, Polish, and more than 20 other languages. It finds many errors that a simple spell checker cannot detect and several grammar problems.

![](https://cdn.rawgit.com/gtarawneh/languagetool-sublime/master/demo.gif)

#### Installation

If you're using Package Control then open up the command palette
(<kbd>ctrl+shift+p</kbd>), type `install`, press Enter then type
`languagetool` and press Enter again.

To get the latest updates before they get released, install via `Package
Control: Add Repository`. This will update your plugin with new commits as
they are being pushed to the repo.

#### Usage

Open the file you want to proof-read then:

1. Run a language check (<kbd>ctrl+shift+c</kbd>). Any problems identified by LanguageTool will be highlighted.
2. Move between the problems using <kbd>alt+down</kbd> (next) and <kbd>alt+up</kbd> (previous).
3. A panel at the bottom will display a brief description  of the highlighted problem and suggest corrections if available.
4. Begin typing to correct the selected problem or press <kbd>alt+shift+f</kbd> to apply the suggested correction.
5. To ignore a problem, press <kbd>alt+d</kbd>.
6. Auto-correcting a problem or ignoring it will move focus to the next problem.

All commands and their keyboard shortcuts are in the command palette with the
prefix `LanguageTool:`.

#### Server Configuration

The adapter POSTs the text to be checked to a LanguageTool server via https.
There are two server settings (local and remote) that can be configured and
one must be selected as default (although command palette variants of `Check
Text` can be used to check text via a specific server).

The remote server is initially configured (in the file `LanguageTool.sublime-
settings`) as `https://languagetool.org:8081/`. There are few limitations on
checking texts using this public server including:

1. Maximum text size of 50Kb
2. Access limited to 20 requests/minute per IP

(See http://wiki.languagetool.org/public-http-api for full details.)

For better performance and to check texts without the above limitations you
can download LanguageTool then run and configure the adapter to use [your own
LanguageTool server](http://wiki.languagetool.org/http-server).

#### License

This plugin is freely available under [GPLv2](https://www.gnu.org/licenses
/old-licenses/gpl-2.0.html) or later.

#### Contributing

Feel free to fork and improve. All contributions are welcome.
