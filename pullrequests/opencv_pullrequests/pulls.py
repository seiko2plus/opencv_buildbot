import json

from twisted.internet import task, reactor
from twisted.internet.defer import inlineCallbacks as callback, returnValue

from .github import Github
from .request import Request
from .config import Config

class Pulls():
    def __init__(self, master):
        self.master = master
        self._started = False
        self._dump_json = '[]'
        self._requests = {}
        self._api = None
        self.stamps = []
        self.db_state = {}

    def getJson(self):
        return self._dump_json

    @callback
    def start(self):
        if self._started:
            raise Exception('Pull already started')
        self._started = True
        yield self._init()
        yield self._poll()
        yield self._update()
        yield self._save()

    @callback
    def _init(self):
        config = self.config
        self.config = Config(self)
        yield self.config.init(config)

        codebases = self.codebases
        for codebase, stamps in codebases.items():
            self.stamps.append(dict(
                codebase=codebase, project=self.project,
                repository=stamps.pop('repository', None),
                revision=stamps.pop('revision', None)
            ))

        api = dict(github=Github)
        if self.service not in api:
            raise Exception('Unsupported api ' + self.service)
        self._api = api[self.service](self.master, self.token, self.agent)
        self.db_state = yield self._getState()

    @callback
    def _poll(self):
        task.deferLater(reactor, self.interval['poll'], self._poll)
        pulls = yield self._api.fetchPulls(self.user, self.repo, self.config_prefix)
        active_ids = set()
        for pr in pulls:
            prid = pr['id']
            active_ids.add(prid)

            if self.filter_pr is not None:
                if not self.filter_pr(pr):
                    continue

            request = self._requests.get(prid, None)
            if request:
                yield request.update(pr)
                continue

            request = Request(self, pr)
            self._requests[prid] = request

            if prid in self.db_state:
                yield request.buildOnState(self.db_state[prid])
            else:
                yield request.build()

        for prid in list(self._requests.keys()):
            if prid in active_ids:
                continue
            request = self._requests.pop(prid)
            yield request.clearBuilds()
            del request

    @callback
    def _update(self):
        task.deferLater(reactor, self.interval['update'], self._update)
        info_list = []
        for k in sorted(self._requests.keys(), reverse=True):
            request = self._requests[k]
            yield request.updateBuilds()
            info_list.append(request.getInfo())
        self._dump_json = json.dumps(info_list, ensure_ascii=False)

    @callback
    def _save(self):
        task.deferLater(reactor, self.interval['save'], self._save)
        states = {}
        for prid, request in self._requests.items():
            states[prid] = request.getState()

        if len(states) > 0:
            yield self._setState(states)

    @callback
    def _getState(self):
        def numric_keys(dt):
            new_dict = {}
            for numstr, val in dt.items():
                new_dict[int(numstr)] = val
            return new_dict

        object_id = yield self._getObjectId()
        db_states = yield self.master.db.state.getState(object_id, 'requests', {})

        for prid, state in db_states.items():
            state['builds'] = numric_keys(state['builds'])
        returnValue(numric_keys(db_states))

    @callback
    def _setState(self, data):
        object_id = yield self._getObjectId()
        yield self.master.db.state.setState(object_id, 'requests', data)

    @callback
    def _getObjectId(self):
        object_id = yield self.master.db.state.getObjectId("%s/%s" % (self.user, self.repo), 'pullrequests')
        returnValue(object_id)