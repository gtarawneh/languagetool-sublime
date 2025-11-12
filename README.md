### LanguageTool for Sublime Text 2/3

#### Overview

This is a simple adapter to integrate
[LanguageTool](https://languagetool.org/) (an open source proof-reading
program) into Sublime Text 2/3.

From <https://www.languagetool.org/>:

> LanguageTool is an Open Source proofreading program for English, French,
> German, Polish, and more than 20 other languages. It finds many errors that
> a simple spell checker cannot detect and several grammar problems.

![languagetol-sublime demo](https://cdn.rawgit.com/gtarawneh/languagetool-sublime/master/demo.gif)

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
3. A panel at the bottom will display a brief description of the highlighted problem and suggest corrections if available.
4. Begin typing to correct the selected problem or press <kbd>alt+shift+f</kbd> to apply the suggested correction.
5. To ignore a problem, press <kbd>alt+d</kbd>.
6. Auto-correcting a problem or ignoring it will move focus to the next problem.

All commands and their keyboard shortcuts are in the command palette with the
prefix `LanguageTool:`.

#### Configuration

The settings file for the plugin can be opened from the `Preferences` menu
(`Preferences` &rarr; `Package Settings` &rarr; `LanguageTool` &rarr;
`Settings - User`). Default settings are in the corresponding submenu item
`Settings - Default`. Note that default settings are provided for reference
and should not be edited as they may be overwritten when the plugin is updated
or reinstalled. Instead, copy and modify any settings you wish to override to
`Settings - User`.

#### Local vs. Remote Checking

The adapter supports local and remote LanguageTool servers. Remote checking is
the default and works by submitting text over https to an api endpoint on
<https://languagetool.org> (this can be changed in plugin settings). This public
service is subject to usage constraints including:

1. 20 requests per IP per minute (this is supposed to be a peak value — don’t
	constantly send this many requests or LanguageTool would have to block you)
2. 75KB text per IP per minute
3. 20KB text per request
4. Only up to 30 misspelled words will have suggestions.
5. No guarantees about performance or availability.
	The limits may change at any time.

(See <https://dev.languagetool.org/public-http-api> for full details.)

Instead of using the public (remote) LanguageTool service, text can be checked
using a local LanguageTool Installation. A local LanguageTool server can be
started by the plugin itself using the command `LanguageTool: Start Local
Server` (this requires the settings entry `languagetool_jar` to point to the
local languagetool JAR file), or from the command line following the
instructions in <https://dev.languagetool.org/http-server>.

The settings file contains remote and local server URL entries. A third option
`default_server` indicates which of these is used when the command
`LanguageTool: Check Text` is ran. As an added convenience, two more commands:

* `LanguageTool: Check Text (Local Server)`
* `LanguageTool: Check Text (Remote Server)`

are provided, which can be used to check text using the local/remote servers
regardless of `default_server`. This can be used for one-off checks when it's
desirable to use a particular server with certain pieces of text.

#### Ignoring specific messages

If you don’t need specific LanguageTool messages, you can ignore them.

The example below shows how to ignore LanguageTool spell checking messages for English and Russian languages. You can follow these steps for ignoring other messages.

1. [Start your local LanguageTool server](https://dev.languagetool.org/http-server#starting-from-command-line) from your terminal:

	```bash
	"path/to/your/binary/java" --class-path "path/to/your/file/languagetool-server.jar" org.languagetool.server.HTTPServer --port 8081
	```

1. Send in another tab of your terminal [the request to the launched local server](https://dev.languagetool.org/http-server#testing-the-server). Query string parameters:

	1. `language` — [the language code](https://github.com/gtarawneh/languagetool-sublime/blob/master/LanguageList.py) of the language of your texts
	1. `text` — the text for which you get the message that you want to ignore

	For example, if you got the message `Possible spelling mistake found` for the text `Nelia Kerechanyn is a goddess` and the message `Возможно найдена орфографическая ошибка` for the text `Неля Керечанин — богиня`, respectively, you should send requests:

	```bash
	http :8081/v2/check language==en-US text=="Nelia Kerechanyn is a goddess"

	http :8081/v2/check language==ru text=="Неля Керечанин — богиня"
	```

	(Examples use [HTTPie](https://httpie.io/) commands.)

1. LanguageTool should return a response to your request in JSON format. Values of the key `matches[].rule.id` of this response are IDs of messages. For requests from the example above, LanguageTool should return IDs `MORFOLOGIK_RULE_EN_US` and `MORFOLOGIK_RULE_RU_RU`.
1. Open Sublime Text → `Preferences` → `Browse packages…` → `User` → create the file `LanguageToolUser.sublime-settings` → create a JSON object with keys `ignored`, `ignored[].description` and `ignored[].id` → save the file. Keys:

	1. `description` — a description of the ignored message. The value should be a string, the format is arbitrary.
	1. `id` — the ID you got in step 3.

	The file `LanguageToolUser.sublime-settings` for the example discussed above:

	```json
	{
		"ignored":
		[
			{
				"description": "Ignore spell checking for English texts",
				"id": "MORFOLOGIK_RULE_EN_US"
			},
			{
				"description": "Ignore spell checking for Russian texts",
				"id": "MORFOLOGIK_RULE_RU_RU"
			}
		]
	}
	```

After these steps languagetool-sublime shouldn’t return messages `Possible spelling mistake found` and `Возможно найдена орфографическая ошибка` at all.

#### License

This plugin is freely available under
[GPLv2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html) or later.

#### Contributing

Feel free to fork and improve. All contributions are welcome.
