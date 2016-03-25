import sublime, sublime_plugin
import re
import xml.etree.ElementTree
import urllib
import urllib2

# problems is an array of n-tuples in the form (x0, x1, msg, description, suggestion)
problems = []

# index of currently selected problem
selProblem = 0

# select characters with indeces [i, j]
def moveCaret(self, i, j):
	target = self.view.text_point(0, i)
	self.view.sel().clear()
	self.view.sel().add(sublime.Region(target, target+j-i))

# returns key of region i
def getProbKey(i):
	return "p" + str(i)

def clearRegions(self):
	v = self.view;
	for i in range(0, len(problems)-1):
		v.clear_region(getProbKey(i))

# select problem i, assumes len(problems)>0
def selectProblem(self, i):
	v = self.view
	if len(problems) > 0:
		c = problems[i]
		regions = v.get_regions(getProbKey(i))
		r = regions[0]
		moveCaret(self, r.a, r.b)
		sublime.status_message(c[3] + " (" + c[4] + ")")

# navigation function
class gotoNextProblemCommand(sublime_plugin.TextCommand):
	def run(self, edit, jumpSizeStr):
		global problems
		global selProblem

		if len(problems) > 0:
			jumpSize = int(jumpSizeStr)
			selProblem = (selProblem + jumpSize) % len(problems)
			selectProblem(self, selProblem)
		else:
			sublime.status_message("run language check first")

class LanguageToolCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global problems
		global selProblem
		problems = []
		v = self.view
		clearRegions(self)
		strText = v.substr(sublime.Region(0, v.size()))
		urlargs = urllib.urlencode({'language' : 'en-US', 'text': strText})
		s = "http://localhost:8081/?" + urlargs
		content = urllib2.urlopen(s).read()
		print(content)
		root = xml.etree.ElementTree.fromstring(content)
		ind = 0;
		for child in root:
			if child.tag == "error":
				a = int(child.attrib["fromx"])
				b = int(child.attrib["tox"])
				category = child.attrib["category"]
				msg = child.attrib["msg"]
				replacements = child.attrib["replacements"]
				v.add_regions(getProbKey(ind), [sublime.Region(a, b)], "comment", "", 0 * sublime.DRAW_OUTLINED)
				problems.append((a, b, category, msg, replacements))
				ind += 1;
		if ind>0:
			selProblem = 0
			selectProblem(self, selProblem)
		else:
			sublime.status_message("No errors found :-)")
