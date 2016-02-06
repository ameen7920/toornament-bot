import json
import urllib2


class Client(object):
    def __init__(self, api_key):
        self.api_key = api_key
        assert self.api_key

    def call(self, path):
        url = 'https://api.toornament.com/v1/{p}'.format(p=path.strip('/'))
        req = urllib2.Request(url, headers={
            'X-Api-Key': self.api_key,
        })
        res = urllib2.urlopen(req)
        return json.loads(res.read())

    def list_participants(self, tid):
        return self.call('tournaments/{id}/participants'.format(id=tid))
