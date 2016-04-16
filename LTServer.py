# contains functions that handle http POST and xml parsing

import sublime
import xml.etree.ElementTree
import urllib

# posts `text` to `server`, returns server response or, when failing, None
def getResponse(server, text, lang):
	if _is_ST2():
		return _getResponse_ST2(server, text, lang)
	else:
		return _getResponse_ST3(server, text, lang)

# parses an xml string
def parseResponse(content):
	if _is_ST2():
		return _parseResponse_ST2(content)
	else:
		return _parseResponse_ST3(content)

# internal functions:

def getPost(text, lang):
	if lang == "autodetect":
		return {'autodetect' : 'yes', 'text': text.encode('utf8')}
	else:
		return {"language": lang, 'text': text.encode('utf8')}

def _is_ST2():
	return (int(sublime.version()) < 3000)

def _getResponse_ST2(server, text, lang):
	data = urllib.urlencode(getPost(text, lang))
	try:
		content = urllib.urlopen(server, data).read()
	except IOError:
		return None
	else:
		return content

def _getResponse_ST3(server, text, lang):
	data = urllib.parse.urlencode(getPost(text, lang))
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
