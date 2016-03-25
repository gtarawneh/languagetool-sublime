import sublime, sublime_plugin
import re
import xml.etree.ElementTree
import urllib
import urllib2


# mistakes is an array of n-tuples in the form (x0, x1, msg, description, suggestion)
mistakes = []

# index of currently selected mistake
selMistake = 0;

# highlight all mistakes
def outlineMistakes():
	for c in mistakes:
		highlight(c[0], c[1]);

# select characters with indeces [i, j]
def moveCaret(self, i, j):
	target = self.view.text_point(0, i)
	self.view.sel().clear()
	self.view.sel().add(sublime.Region(target, target+j-i))

# select mistake i
def selectProblem(self, i):
	if len(mistakes) > 0:
		c = mistakes[i];
		outlineMistakes();
		moveCaret(self, c[0], c[1]);
		sublime.status_message(c[3] + " (" + c[4] + ")")
	else:
		sublime.status_message("run language check first")		

class moveNextMistakeCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global mistakes
		global selMistake

		selMistake += 1
		if selMistake>=len(mistakes):
			selMistake = 0;

		selectProblem(self, selMistake);

class movePrevMistakeCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global mistakes
		global selMistake

		selMistake -= 1
		if selMistake<0:
			selMistake = len(mistakes) - 1;

		selectProblem(self, selMistake);

class HelloWorldCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global mistakes
		global selMistake
		mistakes = [];
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
				mistakes.append((x1,x2, category, msg, replacements));
				highlight(x1, x2);
				errors_found = True;
		if errors_found:
			selMistake = 0;
			selectProblem(self, selMistake);
		else:
			sublime.status_message("No errors found :-)");


	def run_old(self, edit):
		#self.view.insert(edit, 0, "hey there!")
		v = self.view;
		str1 = v.substr(sublime.Region(0, v.size()));
		# print str1
		d = parseContent(str1);
		for word in d:
			if (d[word]>1) and (len(word)>3):
				print("removing: " + word + " (" + str(d[word]) + " occurrenecs)")
				inds = findSubstr(str1, word);
				for i in inds:
					highlight(i, i+len(word), 0);
				# str1 = str1.replace(word, '?' * len(word));
		# self.view.replace(edit, sublime.Region(0, self.view.size()), str1);

def highlight(x0, x1):
	r = sublime.Region(x0, x1);
	v = sublime.active_window().active_view()
	flags = sublime.DRAW_OUTLINED;
	obj1 = v.add_regions("key_test" + str(x0), [r], "comment", "", flags);

def findSubstr(str, substr):
	return [m.start() for m in re.finditer(substr, str)]

def parseContent(str):

	lineArr = str.split("\n");
	f = lambda str : str.rstrip()
	d = dict();

	for ln in lineArr:
		ln2 = ln.rstrip().split(' ');
		for word in ln2:
			if word in d:
				d[word] += 1
			else:
				d[word] = 1

	return d

# interesting:

# this is how to grab some input from the user (return type is object, not sure what that is exactly)

# x = sublime.active_window().show_input_panel("How is it going:", "", 0, None, None)	