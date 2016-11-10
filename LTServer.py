import sublime
import sys
import os
import json

def _is_ST2():
	return (int(sublime.version()) < 3000)

if _is_ST2():
	from urllib import urlencode
	from urllib import urlopen
else:
	from urlparse import urlencode
	from urllib2 import urlopen

def getResponse(server, text, lang, ignoredIDs):
	payload = {
	'language': lang,
	'text': text.encode('utf8'),
	'User-Agent': 'sublime',
	'disabledRules' : ','.join(ignoredIDs)
	}
	content = _post(server, payload)
	if content:
		j = json.loads(content.decode('utf-8'))
		return j['matches']
	else:
		return None

# internal functions:

def _post(server, payload):
	if _is_ST2():
		return _post_ST2(server, payload)
	else:
		return _post_ST3(server, payload)

def _post_ST2(server, payload):
	data = urlencode(payload)
	try:
		content = urlopen(server, data).read()
	except IOError:
		return None
	else:
		return content

def _post_ST3(server, payload):
	data = urlencode(payload)
	data = data.encode('utf8')
	try:
		content = urlopen(server, data).read()
	except IOError:
		return None
	else:
		return content
