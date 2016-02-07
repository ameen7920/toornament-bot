from __future__ import unicode_literals
import json
import urllib2


def send_message(token, chat_id, text):
    if not isinstance(text, basestring):
        text = '\n'.join(text)
    url = 'https://api.telegram.org/bot{t}/sendMessage'.format(t=token)
    req = urllib2.Request(url, data=json.dumps({
        'chat_id': chat_id,
        'text': text,
        'disable_web_page_preview': True,
        'parse_mode': 'Markdown',
    }), headers={
        'Content-Type': 'application/json',
    })
    res = urllib2.urlopen(req)
    return json.loads(res.read())
