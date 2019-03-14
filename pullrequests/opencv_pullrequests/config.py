from twisted.internet.defer import inlineCallbacks as callback, returnValue

class Config():
    def __init__(self, pulls):
        self.master = pulls.master
        self.repo = pulls.repo
        self.project = pulls.project
        self._c = {}

    def get(self, opt, default=None):
        return self._c.get(opt, default)

    @callback
    def allBuilders(self):
        if hasattr(self, '_all_builders'):
            returnValue(self._builders)
        self._all_builders = {}

        builders = yield self.master.data.get(('builders', ))
        for builder in builders:
            self._all_builders[builder['name']] = builder['builderid']

        returnValue(self._all_builders)

    @callback
    def init(self, config):
        all_builders = yield self.allBuilders()
        def builders_ids(builderNames, search=None):
            if not search:
                search = all_builders
            builders = []
            for name in builderNames:
                if name not in search:
                    raise TypeError("builder '%s' not exist" % name)
                builders.append(search[name])
            return builders

        def builder_search(search):
            tp_srch = type(search)
            if tp_srch is dict:
                return zip(search.keys(), builders_ids(search.values()))
            elif tp_srch is list:
                return zip(search, builders_ids(search))
            elif tp_srch is set:
                search = list(search)
                return zip(search, builders_ids(search))
            else:
                raise TypeError(
                    "Unsupported type '%s' Option 'search' in builders only accept dict, list and set"
                    % search_tp
                )
            return {}

        def init_builders(c, o):
            search = o.get('search', None)
            default = o.get('default', None)
            if not search:
               raise Exception("Config %s is builders type which needs 'search' option" % c)
            search = dict(builder_search(search))
            if default:
                default = set(builders_ids(default, search))
            return dict(search=search, default=default)

        def init_sourcestamp(c, o):
            if 'codebase' not in o:
                raise Exception("Config %s is builders type which needs 'codebase' option" % c)
            return dict(codebase=o['codebase'])

        def init_properties(c, o):
            return {}

        type_handler = dict(
            builders=(init_builders, (self._p_builder, self._d_builder)),
            sourcestamp=(init_sourcestamp, (self._p_stamp, self._d_stamp)),
            properties=(init_properties, (self._p_prop, self._d_prop))
        )

        for c, o in config.items():
            tp = o.get('type', 'properties')
            handler = type_handler.get(tp, None)
            if not handler:
                raise Exception("Unknown config type '%s'" % tp)

            ret = dict(
                name=o.get('name', c),
                default=o.get('default', None),
                handler=handler[1]
            )
            ret.update(handler[0](c, o))
            self._c[c] = ret

    def parse(self, pr):
        pr_config = pr.get('config', {})
        ret = (set(), {}, {})  # builderids, stamps, props
        for c, o in self._c.items():
            handler = o['handler']
            val = pr_config.get(c, None)
            if not val or len(val) == 0:
                handler[1](ret, pr, o)
                continue
            handler[0](ret, pr, o, val)
        return ret

    def _d_builder(self, ret, pr, o):
        default = o['default']
        if default is not None:
            ret[0].update(default)

    def _p_builder(self, ret, pr, o, val):
        search = o['search']
        val = val.split(',')
        bids = set()
        for builder in val:
            bid = search.get(builder, None)
            if bid:
                bids.add(bid)
        if len(bids) > 0:
            ret[0].update(bids)
        else:
            self._d_builder(ret, pr, o)

    def _d_stamp(self, ret, pr, o, default={}):
        if len(default) == 0:
            default = o['default']
            if default is None:
                return
        name = o['name']
        stamp = dict(
            codebase=o['codebase'], project=self.project,
            repository="%s/%s.git" % (pr['user_url'], name),
            branch=pr['head_branch']
        )
        stamp.update(default)
        ret[1][name] = stamp

    def _p_stamp(self, ret, pr, o, val):
        val = val.split(',')
        stamp = {}
        for kv in val:
            kv = kv.split(':')
            if len(kv) != 2:
                continue
            name = kv[0]
            if name not in ['repository', 'branch', 'revision']:
                continue
            # todo: too important to validate them
            validate = kv[1]
            stamp[name] = validate
        self._d_stamp(ret, pr, o, stamp)

    def _d_prop(self, ret, pr, o):
        default = o['default']
        if default is not None:
            ret[2][o['name']] = (default, 'default')

    def _p_prop(self, ret, pr, o, val):
        ret[2][o['name']] = (val, "pullrequest %s#%d" % (self.repo, pr['id']))
