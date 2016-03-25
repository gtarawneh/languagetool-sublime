import sublime, sublime_plugin
import re
import xml.etree.ElementTree
import urllib
import urllib2

# problems is an array of n-tuples in the form (x0, x1, msg, description, suggestion)
problems = []

# index of currently selected problem
selProblem = 0;

# outline all problems
def outlineProblems():
	for c in problems:
		outline(c[0], c[1]);

# select characters with indeces [i, j]
def moveCaret(self, i, j):
	target = self.view.text_point(0, i)
	self.view.sel().clear()
	self.view.sel().add(sublime.Region(target, target+j-i))

# select problem i
def selectProblem(self, i):
	if len(problems) > 0:
		c = problems[i];
		outlineProblems();
		moveCaret(self, c[0], c[1]);
		sublime.status_message(c[3] + " (" + c[4] + ")")
	else:
		sublime.status_message("run language check first")		

class gotoNextProblemCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global problems
		global selProblem

		selProblem += 1
		if selProblem>=len(problems):
			selProblem = 0;

		selectProblem(self, selProblem);

class gotoPrevProblemCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global problems
		global selProblem

		selProblem -= 1
		if selProblem<0:
			selProblem = len(problems) - 1;

		selectProblem(self, selProblem);

class LanguageToolCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global problems
		global selProblem
		problems = [];
		v = self.view;
		str1 = v.substr(sublime.Region(0, v.size()));
		self.view.replace(edit, sublime.Region(0, self.view.size()), str1);
		urlargs = urllib.urlencode({'language' : 'en-US', 'text': str1});
		s="http://localhost:8081/?" + urlargs;
		content = urllib2.urlopen(s).read()
		print(content)
		root = xml.etree.ElementTree.fromstring(content)
		errors_found = False;
		for child in root:
			if child.tag == "error":
				x1 = int(child.attrib["fromx"])
				x2 = int(child.attrib["tox"])
				category = child.attrib["category"]
				msg = child.attrib["msg"]
				replacements = child.attrib["replacements"]
				problems.append((x1,x2, category, msg, replacements));
				outline(x1, x2);
				errors_found = True;
		if errors_found:
			selProblem = 0;
			selectProblem(self, selProblem);
		else:
			sublime.status_message("No errors found :-)");

def outline(x0, x1):
	r = sublime.Region(x0, x1);
	v = sublime.active_window().active_view()
	flags = sublime.DRAW_OUTLINED;
	obj1 = v.add_regions("key_test" + str(x0), [r], "comment", "", flags);