# LanguageTool.py
#
# This is a simple Sublime Text plugin for checking grammar. It passes buffer
# content to LanguageTool (via http) and highlights reported problems.

import sublime
import sublime_plugin
import subprocess
import os.path
import fnmatch

def _is_ST2():
	return (int(sublime.version()) < 3000)

if _is_ST2():
	import LTServer
	import LanguageList
else:
	from . import LTServer
	from . import LanguageList

# problems is an array of dictionaries, each being a language problem
problems = []

# list of ignored rules
ignored = []

# highlight scope
hscope = "comment"

# displayMode determines where problem details are printed
# supported modes are 'statusbar' or 'panel'
displayMode = 'statusbar';

# global constants
lt_user_settings_file = 'LanguageToolUser.sublime-settings'
lt_settings_file      ='LanguageTool.sublime-settings'

# select characters with indices [i, j]
def moveCaret(view, i, j):
	target = view.text_point(0, i)
	view.sel().clear()
	view.sel().add(sublime.Region(target, target+j-i))

def setStatusBar(str):
	sublime.status_message(str)

def selectProblem(v, p):
	r = v.get_regions(p['regionKey'])[0]
	moveCaret(v, r.a, r.b)
	v.show_at_center(r)
	showProblem(p)

def problemSolved(v, p):
	rl = v.get_regions(p['regionKey'])
	if len(rl) == 0:
		print('tried to find non-existing region with key ' + p['regionKey'])
		return True
	r = rl[0]
	# a problem is solved when either:
	# 1. its region has zero length
	# 2. its contents have been changed
	return r.empty() or (v.substr(r) != p['orgContent'])

def showProblem(p):
	global displayMode
	if displayMode == 'panel':
		showProblemPanel(p)
	else:
		showProblemStatusBar(p)

def showProblemPanel(p):
	msg = p['message']
	if p['replacements']:
		msg += '\n\nSuggestion(s): ' + ', '.join(p['replacements'])
	if p['urls']:
		msg += '\n\nMore Info: ' + '\n'.join(p['urls'])
	showPanelText(msg)

def showProblemStatusBar(p):
	if p['replacements']:
		msg = u"{0} ({1})".format(p['message'], p['replacements'])
	else:
		msg = p['message']
	sublime.status_message(msg)

def showPanelText(str):
	if _is_ST2():
		window = sublime.active_window();
		pt = window.get_output_panel("languagetool")
		pt.set_read_only(False)
		edit = pt.begin_edit()
		pt.insert(edit, pt.size(), str)
		window.run_command("show_panel", {"panel": "output.languagetool"})
	else:
		sublime.active_window().run_command('set_language_tool_panel_text', {'str': str})

class setLanguageToolPanelTextCommand(sublime_plugin.TextCommand):
	def run(self, edit, str):
		window = sublime.active_window();
		pt = window.get_output_panel("languagetool")
		pt.settings().set("wrap_width", 0)
		pt.settings().set("word_wrap", True)
		pt.set_read_only(False)
		pt.insert(edit, pt.size(), str)
		window.run_command("show_panel", {"panel": "output.languagetool"})

# navigation function
class gotoNextLanguageProblemCommand(sublime_plugin.TextCommand):
	def run(self, edit, jumpForward = True):
		global problems
		v = self.view
		if len(problems) > 0:
			sel = v.sel()[0]
			if jumpForward:
				for p in problems:
					r = v.get_regions(p['regionKey'])[0];
					if (not problemSolved(v, p)) and (sel.begin() < r.a):
						selectProblem(v, p)
						return
			else:
				for p in reversed(problems):
					r = v.get_regions(p['regionKey'])[0];
					if (not problemSolved(v, p)) and (r.a < sel.begin()):
						selectProblem(v, p)
						return
		setStatusBar("no further language problems to fix")
		sublime.active_window().run_command("hide_panel", {"panel": "output.languagetool"})

class clearLanguageProblemsCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		v = self.view
		global problems
		for p in problems:
			v.erase_regions(p['regionKey'])
		problems = []
		recompHighlights(v)
		caretPos = self.view.sel()[0].end()
		v.sel().clear()
		sublime.active_window().run_command("hide_panel", {"panel": "output.languagetool"})
		moveCaret(v, caretPos, caretPos)

class markLanguageProblemSolvedCommand(sublime_plugin.TextCommand):
	def run(self, edit, applyFix):
		global problems
		v = self.view
		sel = v.sel()[0]
		for p in problems:
			r = v.get_regions(p['regionKey'])[0]
			replacements = p['replacements']
			nextCaretPos = r.a;
			if r == sel:
				if applyFix and replacements:
					# fix selected problem:
					if len(replacements)>1:
						callbackF = lambda i : self.onSuggestionListSelect(v, p, replacements, i)
						v.window().show_quick_panel(replacements, callbackF)
						return
					else:
						v.replace(edit, r, replacements[0])
						nextCaretPos = r.a + len(replacements[0])
				else:
					# ignore problem:
					if p['category'] == "Possible Typo":
						# if this is a typo then include all identical typos in the
						# list of problems to be fixed
						pID = lambda py : (py['category'], py['orgContent'])
						ignoreProbs = [px for px in problems if pID(p)==pID(px)]
					else:
						# otherwise select just this one problem
						ignoreProbs = [p]
					for p2 in ignoreProbs:
						ignoreProblem(p2, v, self, edit)
				# after either fixing or ignoring:
				moveCaret(v, nextCaretPos, nextCaretPos) # move caret to end of region
				v.run_command("goto_next_language_problem")
				return
		# if no problems are selected:
		setStatusBar('no language problem selected')

	def onSuggestionListSelect(self, v, p, replacements, choice):
		global problems
		if choice != -1:
			r = v.get_regions(p['regionKey'])[0]
			v.run_command('insert', {'characters': replacements[choice]})
			c = r.a + len(replacements[choice])
			moveCaret(v, c, c) # move caret to end of region
			v.run_command("goto_next_language_problem")
		else:
			selectProblem(v, p)

class startLanguageToolServerCommand(sublime_plugin.TextCommand):
	# sublime.active_window().active_view().run_command('start_language_tool_server')
	def run(self, edit):
		settings = sublime.load_settings(lt_settings_file)
		jarPath = settings.get('languagetool_jar')
		if jarPath:
			if os.path.isfile(jarPath):
				sublime.status_message('Starting local LanguageTool server ...')
				cmd = ['java', '-jar', jarPath, '-t']
				if sublime.platform() == "windows":
					p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, creationflags=subprocess.SW_HIDE)
				else:
					p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			else:
				showPanelText('Error, could not find LanguageTool\'s JAR file (%s)\n\nPlease install LT in this directory or modify the `languagetool_jar` setting.' % jarPath)

class changeLanguageToolLanguageCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global languages
		languages = LanguageList.languages
		languageNames = [x[0] for x in languages]
		onLanguageListSelect_wrapper = lambda i : onLanguageListSelect(i, self.view)
		self.view.window().show_quick_panel(languageNames, onLanguageListSelect_wrapper)

def onLanguageListSelect(i, view):
	global languages
	l = languages[i][1]
	s = view.settings()
	key = 'language_tool_language'
	if i==0:
		s.erase(key)
	else:
		s.set(key, l)

def getLanguage(view):
	s = view.settings()
	key = 'language_tool_language'
	return s.get(key, 'auto')

def ignoreProblem(p, v, self, edit):
	# change region associated with this problem to a 0-length region
	r = v.get_regions(p['regionKey'])[0]
	dummyRg = sublime.Region(r.a, r.a)
	v.add_regions(p['regionKey'], [dummyRg], hscope, "", sublime.DRAW_OUTLINED)
	# dummy edit to enable undoing ignore
	v.insert(edit, v.size(), "")

def loadIgnoredRules():
	settings = sublime.load_settings(lt_user_settings_file)
	return settings.get('ignored', [])

def saveIgnoredRules(ignored):
	settings = sublime.load_settings(lt_user_settings_file)
	settings.set('ignored', ignored)
	sublime.save_settings(lt_user_settings_file)

def getServer(settings, forceServer):
	# returns server url based on the setting `default_server`
	#
	# If `default_server` is `local` then return the server defined in
	# `language_server_local` (defaults to 'http://localhost:8081/v2/check').
	#
	# If `default_server` is `remote` then return the server defined in
	# `language_server_remote` (defaults to 'https://languagetool.org/api/v2/check').
	#
	# if `default_server` is anything else then treat as `remote`
	#
	if forceServer is None:
		forceServer = settings.get('default_server', 'remote')
	if forceServer == "local":
		server = settings.get('languagetool_server_local', 'http://localhost:8081/v2/check')
	else:
		server = settings.get('languagetool_server_remote', 'https://languagetool.org/api/v2/check')
	return server

class LanguageToolCommand(sublime_plugin.TextCommand):
	def run(self, edit, forceServer = None):
		global problems
		global displayMode
		global ignored
		global hscope
		v = self.view
		settings = sublime.load_settings(lt_settings_file)
		server = getServer(settings, forceServer)
		displayMode = settings.get('display_mode', 'statusbar')
		hscope = settings.get("highlight-scope", "comment")
		ignored = loadIgnoredRules()
		strText = v.substr(sublime.Region(0, v.size()))
		checkRegion = v.sel()[0]
		if checkRegion.empty():
			checkRegion = sublime.Region(0, v.size())
		v.run_command("clear_language_problems")
		lang = getLanguage(v)
		ignoredIDs = [rule['id'] for rule in ignored]
		matches = LTServer.getResponse(server, strText, lang, ignoredIDs)
		if matches == None:
			setStatusBar('could not parse server response (may be due to quota if using http://languagetool.org)')
			return
		for match in matches:
			problem = {
				'category': match['rule']['category']['name'],
				'message': match['message'],
				'replacements': [r['value'] for r in match['replacements']],
				'rule' : match['rule']['id'],
				'urls' : [w['value'] for w in match['rule'].get('urls', [])],
			}
			offset = match['offset']
			length = match['length']
			region = sublime.Region(offset, offset + length)
			if not checkRegion.contains(region):
				continue
			ignored_scopes = settings.get('ignored-scopes', [])
			# view.scope_name() returns a string of space-separated scope names
			# (ending with a space)
			pscopes = v.scope_name(region.a).split(' ')[0:-1]
			for ps in pscopes:
				if any([fnmatch.fnmatch(ps, i) for i in ignored_scopes]):
					ignored = True
					break
			else:
				# none of this region's scopes are ignored
				regionKey = str(len(problems))
				v.add_regions(regionKey, [region], hscope, "", sublime.DRAW_OUTLINED)
				problem['orgContent'] = v.substr(region)
				problem['regionKey'] = regionKey
				problems.append(problem)
		if problems:
			selectProblem(v, problems[0])
		else:
			setStatusBar("no language problems were found :-)")

class DeactivateRuleCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global problems
		global ignored
		v = self.view
		sel = v.sel()[0]
		selected = [p for p in problems if sel.contains(v.get_regions(p['regionKey'])[0])]
		if not selected:
			setStatusBar('select a problem to deactivate its rule')
		elif len(selected) == 1:
			rule = {
				"id" : selected[0]['rule'],
				"description" : selected[0]['message']
			}
			ignored.append(rule)
			ignoredProblems = [p for p in problems if p['rule'] == rule['id']]
			for p in ignoredProblems:
				ignoreProblem(p, v, self, edit)
			problems = [p for p in problems if p['rule'] != rule['id']]
			v.run_command("goto_next_language_problem")
			saveIgnoredRules(ignored)
			setStatusBar('deactivated rule %s' % rule)
		else:
			setStatusBar('there are multiple selected problems; select only one to deactivate')

class ActivateRuleCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global ignored
		if ignored:
			activate_callback_wrapper = lambda i : self.activate_callback(i)
			ruleList = [[rule['id'], rule['description']] for rule in ignored]
			self.view.window().show_quick_panel(ruleList, activate_callback_wrapper)
		else:
			setStatusBar('there are no ignored rules')

	def activate_callback(self, i):
		global ignored
		if i != -1:
			activate_rule = ignored[i]
			ignored.remove(activate_rule)
			saveIgnoredRules(ignored)
			setStatusBar('activated rule %s' % activate_rule['id'])

class LanguageToolListener(sublime_plugin.EventListener):
	def on_modified(self, view):
		# buffer text was changed, recompute region highlights
		recompHighlights(view)

def recompHighlights(view):
	global problems
	for p in problems:
		rL = view.get_regions(p['regionKey'])
		if rL:
			regionScope = "" if problemSolved(view, p) else hscope
			view.add_regions(p['regionKey'], rL, regionScope, "",  sublime.DRAW_OUTLINED)
