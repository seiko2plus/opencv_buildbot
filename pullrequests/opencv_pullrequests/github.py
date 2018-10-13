import re
from twisted.internet.defer import inlineCallbacks as callback, returnValue
from buildbot.util.httpclientservice import HTTPClientService

class Github():
    def __init__(self, master, token=None, agent=None):
        self.http_service = None
        self.http_headers = {'User-Agent': 'Buildbot Github'}
        self.http_url = 'https://api.github.com'
        self.master = master
        if token:
            self.http_headers['Authorization'] =  'token ' + token
        if agent:
            self.http_headers['User-Agent'] = agent

    @callback
    def fetch(self, url):
        if not self.http_service:
            self.http_service = yield HTTPClientService.getService(self.master, self.http_url, headers=self.http_headers)

        result = yield self.http_service.get(url)
        if result.code != 200:
            raise Exception("invalid status %d -> %s" % (result.code, url))

        json = yield result.json()
        returnValue(json)

    @callback
    def fetchPulls(self, user, repo, config_prefix = ''):
        fetch = yield self.fetch("/repos/%s/%s/pulls?state=open" % (user, repo))
        if not fetch:
            returnValue([])
        pulls = []
        for pr in fetch:
            try:
                new_pr = {}
                new_pr['id'] = int(pr['number'])
                new_pr['title'] = pr['title']
                new_pr['body'] = pr['body']
                new_pr['url'] = pr['html_url']
                new_pr['author'] = pr['user']['login']
                new_pr['assignee'] = pr['assignee']['login'] if pr['assignee'] else None
                #new_pr['user'] = pr['head']['repo']['owner']['login']
                new_pr['user'] = new_pr['author']
                new_pr['user_url'] = pr['user']['html_url']
                new_pr['base_url'] = pr['base']['repo']['clone_url']
                new_pr['base_branch'] = pr['base']['ref']
                new_pr['head_url'] = pr['head']['repo']['clone_url']
                new_pr['head_branch'] = pr['head']['ref']
                new_pr['head_sha'] = pr['head']['sha']
                new_pr['updated_at'] = pr['updated_at']
                new_pr['config'] = self._parseConfig(config_prefix, pr['body'])
                pulls.append(new_pr)
            except Exception as e:
                print("Unable to parse pr: %s ->" % str(e))
                print(pr)
        returnValue(pulls)

    def _parseConfig(self, config_prefix, body):
        parse_it = False
        config = {}
        prefix_len = len(config_prefix)

        for line in body.split('\r\n'):
            if line.startswith('``'):
                parse_it = False if parse_it else True
                continue
            if not parse_it:
                continue

            line = re.sub(r"\s+", '', line)
            name_val = line.split('=')
            if len(name_val) != 2:
                continue

            config_name = name_val[0]
            if prefix_len >= len(config_name):
                continue
            if not config_name.startswith(config_prefix) or config_name.startswith('#'):
                continue

            config[config_name[prefix_len:]] = name_val[1]

        return config





