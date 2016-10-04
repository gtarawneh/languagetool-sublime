import sublime
import urllib

import sys
import os
import json

def getResponse(server, text, lang, ignored):
	payload = {
	'language': lang,
	'text': text.encode('utf8'),
	'User-Agent': 'sublime',
	'disabledRules' : ','.join(ignored)
	}
	content = _post(server, payload)
	if content:
		j = json.loads(content.decode('utf-8'))
		return j['matches']
	else:
		return None

# internal functions:

def _is_ST2():
	return (int(sublime.version()) < 3000)

def _post(server, payload):
	if _is_ST2():
		return _post_ST2(server, payload)
	else:
		return _post_ST3(server, payload)

def _post_ST2(server, payload):
	data = urllib.urlencode(payload)
	try:
		content = urllib.urlopen(server, data).read()
	except IOError:
		return None
	else:
		return content

def _post_ST3(server, payload):
	data = urllib.parse.urlencode(payload)
	data = data.encode('utf8')
	try:
		content = urllib.request.urlopen(server, data).read()
	except IOError:
		return None
	else:
		return content
