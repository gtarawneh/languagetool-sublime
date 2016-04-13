# contains functions that handle http POST and xml parsing

import sublime
import xml.etree.ElementTree
import urllib

# posts `text` to `server`, returns server response or, when failing, None
def getResponse(server, text):
	if _is_ST2():
		return _getResponse_ST2(server, text)
	else:
		return _getResponse_ST3(server, text)

# parses an xml string
def parseResponse(content):
	if _is_ST2():
		return _parseResponse_ST2(content)
	else:
		return _parseResponse_ST3(content)

# internal functions:

def _is_ST2():
	return (int(sublime.version()) < 3000)

def _getResponse_ST2(server, text):
	data = urllib.urlencode({'autodetect' : 'yes', 'text': text.encode('utf8')})
	try:
		content = urllib.urlopen(server, data).read()
	except IOError:
		return None
	else:
		return content

def _getResponse_ST3(server, text):
	data = urllib.parse.urlencode({'autodetect' : 'yes', 'text': text.encode('utf8')})
	data = data.encode('utf8')
	try:
		content = urllib.request.urlopen(server, data).read()
	except IOError:
		return None
	else:
		return content

def _parseResponse_ST2(content):
	try:
		root = xml.etree.ElementTree.fromstring(content)
	except xml.parsers.expat.ExpatError:
		return None
	else:
		return root

def _parseResponse_ST3(content):
	try:
		root = xml.etree.ElementTree.fromstring(content)
	except: # TODO: add exception
		return None
	else:
		return root
