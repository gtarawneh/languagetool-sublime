# LanguageTool.py
#
# This is a simple Sublime Text plugin for checking grammar. It passes buffer
# content to LanguageTool (via http) and highlights reported problems.

import sublime
import sublime_plugin

def _is_ST2():
	return (int(sublime.version()) < 3000)

if _is_ST2():
	import LTServer
	import LanguageList
else:
	from . import LTServer
	from . import LanguageList

# problems is an array of n-tuples in the form
# (x0, x1, msg, description, replacements, regionID, orgContent)
problems = []

# displayMode determines where problem details are printed
# supported modes are 'statusbar' or 'panel'
displayMode = 'statusbar';

# select characters with indices [i, j]
def moveCaret(view, i, j):
	target = view.text_point(0, i)
	view.sel().clear()
	view.sel().add(sublime.Region(target, target+j-i))

def setStatusBar(str):
	sublime.status_message(str)

def clearProblems(v):
	global problems
	for p in problems:
		v.erase_regions(p['regionKey'])
	problems = []
	recompHighlights(v)

def selectProblem(v, p):
	r = v.get_regions(p['regionKey'])[0]
	moveCaret(v, r.a, r.b)
	v.show_at_center(r)
	showProblem(p)
	printProblem(p)

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
	msg += '\n\nrule id: ' + p['rule']
	showPanelText(msg)

def showProblemStatusBar(p):
	if replacements == []:
		msg = msg
	else:
		msg = u"{0} ({1})".format(p['message'], p['replacements'])
	sublime.status_message(msg)

def showPanelText(str):
	if (_is_ST2()):
		showPanelTextST2(str)
	else:
		sublime.active_window().run_command('set_language_tool_panel_text', {'str': str})

def showPanelTextST2(str):
	window = sublime.active_window();
	pt = window.get_output_panel("languagetool")
	pt.set_read_only(False)
	edit = pt.begin_edit()
	pt.insert(edit, pt.size(), str)
	window.run_command("show_panel", {"panel": "output.languagetool"})

class setLanguageToolPanelTextCommand(sublime_plugin.TextCommand):
	def run(self, edit, str):
		window = sublime.active_window();
		pt = window.get_output_panel("languagetool")
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

def onSuggestionListSelect(v, p, replacements, choice):
	global problems
	if choice != -1:
		r = v.get_regions(p['regionKey'])[0]
		v.run_command('insert', {'characters': replacements[choice]})
		c = r.a + len(replacements[choice])
		moveCaret(v, c, c) # move caret to end of region
		v.run_command("goto_next_language_problem")
	else:
		selectProblem(v, p)

class clearLanguageProblemsCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global problemSolved
		clearProblems(self.view)

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
						callbackF = lambda i : onSuggestionListSelect(v, p, replacements, i)
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
	v.add_regions(p['regionKey'], [dummyRg], "string", "", sublime.DRAW_OUTLINED)
	# dummy edit to enable undoing ignore
	v.insert(edit, v.size(), "")

class LanguageToolCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global problems
		global displayMode
		v = self.view
		clearProblems(v)
		settings = sublime.load_settings("LanguageTool.sublime-settings")
		server = settings.get('languagetool_server', 'https://languagetool.org:8081/')
		displayMode = settings.get('display_mode', 'statusbar')
		strText = v.substr(sublime.Region(0, v.size()))
		checkRegion = v.sel()[0]
		if checkRegion.empty():
			checkRegion = sublime.Region(0, v.size())
		lang = getLanguage(v)
		matches = LTServer.getResponse(server, strText, lang)
		if matches == None:
			setStatusBar('could not parse server response (may be due to quota if using http://languagetool.org)')
			return
		for match in matches:
			problem = {
			'category': match['rule']['category']['name'],
			'message': match['message'],
			'replacements': [r['value'] for r in match['replacements']],
			'rule' : match['rule']['id'],
			'urls' : [v['value'] for v in match['rule'].get('urls', [])],
			}
			offset = match['offset']
			length = match['length']
			region = sublime.Region(offset, offset + length)
			if checkRegion.contains(region):
				regionKey = str(len(problems))
				v.add_regions(regionKey, [region], "string", "", sublime.DRAW_OUTLINED)
				problem['orgContent'] = v.substr(region)
				problem['regionKey'] = regionKey
				# p = (a, b, category, message, replacements, regionKey, orgContent, urls, rule)
				problems.append(problem)
				printProblem(problem)
		if len(problems) > 0:
			selectProblem(v, problems[0])
		else:
			setStatusBar("no language problems were found :-)")

class LanguageToolListener(sublime_plugin.EventListener):
	def on_modified(self, view):
		# buffer text was changed, recompute region highlights
		recompHighlights(view)

def recompHighlights(view):
	for p in problems:
		rL = view.get_regions(p['regionKey'])
		if len(rL) > 0:
			regionScope = "" if problemSolved(view, p) else "string"
			view.add_regions(p['regionKey'], rL, regionScope, "",  sublime.DRAW_OUTLINED)
