from twisted.internet.defer import inlineCallbacks as callback, returnValue
from buildbot.process import results
from buildbot.db.buildrequests import AlreadyClaimedError

ST_UNKNOWN = 0
ST_PENDING = 1
ST_SUCCESS = 2
ST_WARNINGS = 3
ST_FAILURE = 4
ST_SKIPPED = 5
ST_EXCEPTION = 6
ST_RETRY = 7
ST_CANCELLED = 8

class Request():
    def __init__(self, pulls, pr):
        self.builds = {}
        self.baseStamps = []
        self.pulls = pulls
        self.pr = pr
        self.builders, self.stamps, self.props = pulls.config.parse(pr)
        self._reason = 'pullrequest #%d'% pr['id']
        self._updateBaseStamps()

    def getState(self):
        return dict(
            builds=self.builds,
            props=self.props,
            stamps=self.stamps,
            head_sha=self.pr['head_sha'],
            base_branch=self.pr['base_branch']
        )

    def getInfo(self):
        info = {}
        for r in ['id', 'title', 'url', 'author', 'assignee', 'base_branch']:
            info[r] = self.pr[r]
        info['builds'] = self.builds
        return info

    @callback
    def update(self, pr):
        builders, stamps, props = self.pulls.config.parse(pr)

        if self._isChanged(pr, stamps, props):
            self.props = props
            self.stamps = stamps
            yield self.clearBuilds()

        self.pr = pr
        self.builders = builders
        yield self.build()

    @callback
    def build(self):
        builders = list(self.builders - set(self.builds.keys()))
        if len(builders) == 0:
            returnValue(None)

        bsid, brids = yield self.pulls.master.data.updates.addBuildset(
            scheduler='pullrequests', waited_for=False, reason=self._reason,
            sourcestamps=self.baseStamps + list(self.stamps.values()),
            properties=self.props, builderids=builders
        )

        for bid, rid in brids.items():
            self.builds[bid] = (rid, None, ST_UNKNOWN)

    @callback
    def buildOnState(self, state):
        if not self._isChanged(state, state['stamps'], state['props']):
            builds = state['builds']
            for builder in self.builders:
                if builder in builds:
                    self.builds[builder] = builds[builder]
        yield self.build()

    @callback
    def rebuild(self):
        yield self.clearBuilds()
        yield self.build()

    @callback
    def clearBuilds(self, builders=[]):
        if len(builders) == 0:
            builders = list(self.builds.keys())

        master = self.pulls.master
        for builder in builders:
            rid, cid, status = self.builds.pop(builder)
            if status > ST_PENDING:
                continue

            bid = 0
            if not cid:
                try:
                    b = yield master.db.buildrequests.claimBuildRequests(brids=[rid])
                except AlreadyClaimedError:
                    bid = b['buildid']
            else:
                b = yield master.db.builds.getBuildByNumber(builder, cid)
                bid = b['id']

            if bid:
                master.mq.produce(('control', 'builds', str(bid), 'stop'),
                    dict(reason='rebuild, changes on pr during build'))
            else:
                yield master.data.updates.completeBuildRequests([rid], results.CANCELLED)

    @callback
    def updateBuilds(self):
        for builder in list(self.builds.keys()):
            build = self.builds[builder]
            self.builds[builder] = (yield self.updateBuild(build[0]))

    @callback
    def updateBuild(self, rid):
        breq = yield self.pulls.master.db.builds.getBuilds(buildrequestid=rid)
        if not breq:
            returnValue((rid, None, ST_UNKNOWN))

        breq = breq[-1]
        result = breq['results']
        status = ST_UNKNOWN

        if not breq['complete_at'] and breq['masterid']:
            status = ST_PENDING
        elif result == 0:
            status = ST_SUCCESS
        elif result >= 1 and result <= 6:
            status = result + ST_SUCCESS

        return (rid, breq['number'], status)


    def _updateBaseStamps(self):
        self.baseStamps = self.pulls.stamps.copy()
        for stamp in self.baseStamps:
            stamp['branch'] = self.pr['base_branch']

    def _isPropsChanged(self, props):
        if len(self.props) != len(props):
            return True
        for name, val in self.props.items():
            if name not in props or val[0] != props[name][0]:
                return True
        return False

    def _isStampsChanged(self, stamps):
        if len(self.stamps) != len(stamps):
            return True

        for name, val in self.stamps.items():
            cmp_stamp = stamps.get(name, None)
            if val != cmp_stamp:
                return True
        return False

    def _isChanged(self, pr, stamps, props):
        if self.pr['base_branch'] != pr['base_branch']:
            self._updateBaseStamps()
            return True
        if self.pr['head_sha'] != pr['head_sha']:
            return True
        if self._isPropsChanged(props):
            return True
        if self._isStampsChanged(stamps):
            return True
        return False