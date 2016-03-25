import sublime, sublime_plugin
import re
import xml.etree.ElementTree
import urllib
import urllib2

# problems is an array of n-tuples in the form (x0, x1, msg, description, suggestion)
problems = []

# index of currently selected problem
selProblem = 0;

# select characters with indeces [i, j]
def moveCaret(self, i, j):
	target = self.view.text_point(0, i)
	self.view.sel().clear()
	self.view.sel().add(sublime.Region(target, target+j-i))

# select problem i, assumes len(problems)>0
def selectProblem(self, i):
	if len(problems) > 0:
		c = problems[i];
		moveCaret(self, c[0], c[1]);
		sublime.status_message(c[3] + " (" + c[4] + ")")

# navigation function
class gotoNextProblemCommand(sublime_plugin.TextCommand):
	def run(self, edit, jumpSizeStr):
		global problems
		global selProblem

		if len(problems) > 0:
			jumpSize = int(jumpSizeStr);
			selProblem = (selProblem + jumpSize) % len(problems)
			selectProblem(self, selProblem);
		else:
			sublime.status_message("run language check first")

class LanguageToolCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global problems
		global selProblem
		problems = [];
		v = self.view;
		str1 = v.substr(sublime.Region(0, v.size()));
		urlargs = urllib.urlencode({'language' : 'en-US', 'text': str1});
		s = "http://localhost:8081/?" + urlargs;
		content = urllib2.urlopen(s).read()
		print(content)
		root = xml.etree.ElementTree.fromstring(content)
		for child in root:
			if child.tag == "error":
				x1 = int(child.attrib["fromx"])
				x2 = int(child.attrib["tox"])
				category = child.attrib["category"]
				msg = child.attrib["msg"]
				replacements = child.attrib["replacements"]
				v.add_regions("problem" + str(x1), [sublime.Region(x1, x2)], "comment", "", sublime.DRAW_OUTLINED);
				problems.append((x1,x2, category, msg, replacements));
		if len(problems)>0:
			selProblem = 0;
			selectProblem(self, selProblem);
		else:
			sublime.status_message("No errors found :-)");
