# LanguageTool.py
#
# This is a simple Sublime Text plugin for checking grammar. It passes buffer
# content to LanguageTool (via http) and highlights reported problems.

import sublime, sublime_plugin
import xml.etree.ElementTree
import urllib

# problems is an array of n-tuples in the form
# (x0, x1, msg, description, suggestions, regionID, orgContent)
problems = []

# select characters with indices [i, j]
def moveCaret(self, i, j):
	target = self.view.text_point(0, i)
	self.view.sel().clear()
	self.view.sel().add(sublime.Region(target, target+j-i))

# returns key of region i
def getProbKey(i):
	return "p" + str(i)

# wrapper
def msg(str):
	sublime.status_message(str)

def clearProblems(self):
	global problems
	v = self.view
	for i in range(0, len(problems)):
		v.erase_regions(getProbKey(i))
	problems = []

def selectProblem(self, p):
	v = self.view
	r = v.get_regions(p[5])[0]
	moveCaret(self, r.a, r.b)
	v.show_at_center(r)
	if len(p[4])>0:
		msg("{0} ({1})".format(p[3], p[4]))
	else:
		msg(p[3])

def problemSolved(v, p):
	rl = v.get_regions(p[5])
	if len(rl) == 0:
		print('tried to find non-existing region with key ' + p[5])
		return True
	r = rl[0]
	# a problem is solved when either:
	# 1. its region has zero length
	# 2. its contents have been changed
	return r.empty() or (v.substr(r) != p[6])

# navigation function
class gotoNextLanguageProblemCommand(sublime_plugin.TextCommand):
	def run(self, edit, jumpForward):
		global problems
		if len(problems) > 0:
			caretPos = self.view.sel()[0].begin()
			probInds = range(0, len(problems))
			if jumpForward:
				for ind in probInds: # forward search
					p = problems[ind]
					r = self.view.get_regions(p[5])[0];
					if (not problemSolved(self.view, p)) and (r.a > caretPos):
						selectProblem(self, p)
						return
			else:
				for ind in reversed(probInds): # backward search
					p = problems[ind]
					r = self.view.get_regions(p[5])[0];
					if (not problemSolved(self.view, p)) and (r.a < caretPos):
						selectProblem(self, p)
						return
		msg("no further language problems to fix")

def onSuggestionListSelect(self, edit, p, suggestions, choice):
	global problems
	if choice != -1:
		r = self.view.get_regions(p[5])[0]
		self.view.replace(edit, r, suggestions[choice])
		c = r.a + len(suggestions[choice])
		moveCaret(self, c, c) # move caret to end of region
		self.view.run_command("goto_next_language_problem", {"jumpForward": True})
	else:
		selectProblem(self, p)

class markLanguageProblemSolvedCommand(sublime_plugin.TextCommand):
	def run(self, edit, applyFix):
		global problems
		v = self.view
		sel = v.sel()[0]
		for p in problems:
			r = v.get_regions(p[5])[0]
			nextCaretPos = r.b;
			if (r.a, r.b) == (sel.begin(), sel.end()):
				if applyFix and (len(p[4])>0):
					if '#' in p[4]: # multiple suggestions
						suggestions = p[4].split('#')
						f1 = lambda i : onSuggestionListSelect(self, edit, p, suggestions, i)
						v.window().show_quick_panel(suggestions, f1)
						return
					else: # single suggestion
						v.replace(edit, r, p[4]) # apply correction
						nextCaretPos = r.a + len(p[4])
				else:
					v.insert(edit, v.size(), "") # dummy edit to enable undoing ignore
					dummyR = sublime.Region(r.a, r.a)
					v.add_regions(p[5], [dummyR], "string", "", sublime.DRAW_OUTLINED)
				moveCaret(self, nextCaretPos, nextCaretPos) # move caret to end of region
				v.run_command("goto_next_language_problem", {"jumpForward": True})
				return
		msg('no language problem selected')

class LanguageToolCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global problems
		clearProblems(self)
		settings = sublime.load_settings("languagetool.sublime-settings")
		server = settings.get('languagetool_server', 'https://languagetool.org:8081/')
		v = self.view
		strText = v.substr(sublime.Region(0, v.size()))
		data = urllib.urlencode({'language' : 'en-US', 'text': strText.encode('utf8')})
		try:
			content = urllib.urlopen(server, data).read()
		except IOError:
			msg('error, unable to connect via http, is LanguageTool running?')
		else:
			root = xml.etree.ElementTree.fromstring(content)
			ind = 0;
			for child in root:
				if child.tag == "error":
					ax = int(child.attrib["fromx"])
					ay = int(child.attrib["fromy"])
					bx = int(child.attrib["tox"])
					by = int(child.attrib["toy"])
					a = v.text_point(ay, ax);
					b = v.text_point(by, bx);
					category = child.attrib["category"]
					message = child.attrib["msg"]
					replacements = child.attrib["replacements"]
					region = sublime.Region(a, b)
					regionKey = getProbKey(ind)
					v.add_regions(regionKey, [region], "string", "", sublime.DRAW_OUTLINED)
					orgContent = v.substr(region)
					p = (a, b, category, message, replacements, regionKey, orgContent)
					problems.append(p)
					ind += 1
			if ind>0:
				selectProblem(self, problems[0])
			else:
				msg("no language problems were found :-)")

class LanguageToolListener(sublime_plugin.EventListener):
	def on_modified(self, view):
		# buffer text was changed, recompute region highlights
		for p in problems:
			rL = view.get_regions(p[5])
			if len(rL) > 0:
				regionScope = "" if problemSolved(view, p) else "string"
				view.add_regions(p[5], rL, regionScope, "",  sublime.DRAW_OUTLINED)
