import json
import urllib
import urllib2


class Client(object):
    def __init__(self, api_key):
        self.api_key = api_key
        assert self.api_key

    def call(self, path, query):
        url = 'https://api.toornament.com/v1/{p}'.format(p=path.strip('/'))
        if query:
            url += '?' + urllib.urlencode(query)
        req = urllib2.Request(url, headers={
            'X-Api-Key': self.api_key,
        })
        res = urllib2.urlopen(req)
        return json.loads(res.read())

    def list_participants(self, tournamet_id):
        return self.call('tournaments/{id}/participants'.format(id=tournamet_id))

    def list_matches(self, tournamet_id, participant_id):
        return self.call('tournaments/{id}/matches'.format(id=tournamet_id), {
            'participant_id': participant_id
        })
