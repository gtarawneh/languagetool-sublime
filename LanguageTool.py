# LanguageTool.py
#
# This is a simple Sublime Text plugin for checking grammar. it passes buffer
# content to LanguageTool (via http) and highlights reported problems.

import sublime, sublime_plugin
import xml.etree.ElementTree
import urllib

# problems is an array of n-tuples in the form
# (x0, x1, msg, description, suggestions, regionID)
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
	if len(p[4])>0:
		msg("{0} ({1})".format(p[3], p[4]))
	else:
		msg(p[3])			

# check if string contains any unicode chars
def containsUnicode(str):
	try:
		str.decode('ascii') 
		return False
	except UnicodeEncodeError:
		return True

def problemSolved(self, p):
	r = self.view.get_regions(p[5])[0]
	return (r.a == r.b)

# navigation function
class gotoNextLanguageProblemCommand(sublime_plugin.TextCommand):
	def run(self, edit, jumpSizeStr):
		global problems
		if len(problems) > 0:
			jumpSize = int(jumpSizeStr)
			caretPos = self.view.sel()[0].begin()
			probInds = range(0, len(problems))
			if jumpSize>0:
				for ind in probInds: # forward search
					p = problems[ind]
					r = self.view.get_regions(p[5])[0];
					if (not problemSolved(self, p)) and (r.a > caretPos):
						selectProblem(self, p)
						return
			else:
				for ind in reversed(probInds): # backward search
					p = problems[ind]
					r = self.view.get_regions(p[5])[0];
					if (not problemSolved(self, p)) and (r.a < caretPos):
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
		problems.remove(p)
		self.view.run_command("goto_next_problem", {"jumpSizeStr": "+1"})
	else:
		selectProblem(self, p)

class markLanguageProblemSolvedCommand(sublime_plugin.TextCommand):
	def run(self, edit, applyFix):
		global problems
		sel = self.view.sel()[0]
		for p in problems:
			r = self.view.get_regions(p[5])[0]
			if (r.a, r.b) == (sel.begin(), sel.end()):
				if (applyFix == "True") and (len(p[4])>0):
					if '#' in p[4]:
						suggestions = p[4].split('#')
						f1 = lambda i : onSuggestionListSelect(self, edit, p, suggestions, i)
						self.view.window().show_quick_panel(suggestions, f1)
						return
					else:
						self.view.replace(edit, r, p[4]) # apply correction
				self.view.erase_regions(p[5]) # remove outline
				c = r.a + len(p[4]);
				moveCaret(self, c, c) # move caret to end of region
				problems.remove(p)
				self.view.run_command("goto_next_problem", {"jumpSizeStr": "+1"})
				return
		print('no language problem selected')

class LanguageToolCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global problems
		clearProblems(self)
		v = self.view
		strText = v.substr(sublime.Region(0, v.size()))
		if containsUnicode(strText):
			msg('text contains unicode, unable to pass to LanguageTool')
		else:
			data = urllib.urlencode({'language' : 'en-US', 'text': strText})
			url = "http://localhost:8081/"
			try:
				content = urllib.urlopen(url, data).read()
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
						regionKey = getProbKey(ind)
						v.add_regions(regionKey, [sublime.Region(a, b)], "string", "", sublime.DRAW_OUTLINED)
						problems.append((a, b, category, message, replacements, regionKey))
						ind += 1
				if ind>0:
					selectProblem(self, problems[0])
				else:
					msg("no language problems were found :-)")
