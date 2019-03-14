from twisted.internet import defer, task, reactor
from twisted.internet.defer import inlineCallbacks as callback, returnValue
from twisted.web.static import File

from klein import Klein

from buildbot.www.plugin import Application
from .pulls import Pulls

class TheApp(Application):
    api = Klein()
    pulls = {}
    already_set = False

    def __init__(self, modulename, description, ui=True):
        Application.__init__(self, modulename, description, ui)
        self.resource = self.api.resource()

    def setConfiguration(self, config_list):
        if self.already_set:
            print('pullrequests: configuration already set')
            return

        self.already_set = True

        requires = dict(
            name='',
            caption='',
            user='',
            repo='',
            codebases={}
        )

        default = dict(
            icon='exclamation-circle',
            project='',
            config_prefix='',
            config={},
            interval=dict(poll=60 * 2, update=10, save=60 * 60 * 10),
            token=None,
            service='github',
            agent='Buildbot Pullrequests',
            filter_pr=None
        )

        for config in config_list:
            pull = Pulls(self.master)

            self._setOptions(pull, requires, config, False)
            self._setOptions(pull, default, config)

            for opt in config.keys():
                raise TypeError("Unknown option '%s'" % opt)

            if pull.name in self.pulls:
                raise Exception("Name '%s' already exist" % pull.name)

            self.pulls[pull.name] = pull

        accessible_by_web = ['name', 'caption', 'icon']
        config_list.clear()
        for pull in self.pulls.values():
            config = {}
            for attr in accessible_by_web:
                if hasattr(pull, attr):
                    config[attr] = getattr(pull, attr)
            config_list.append(config)

        self._startAll()

    def _setOptions(self, obj, options, config, default=True):
        for opt, null in options.items():
            if default:
                if opt not in config:
                    setattr(obj, opt, null)
                    continue
            else:
                if opt not in config:
                    raise TypeError("Option '%s' need it" % opt)

            val = config.pop(opt)
            tp = type(null)

            if opt != 'filter_pr' and type(val) != tp:
                raise TypeError("Option '%s' must be a '%s'" % (opt, tp))

            if not default:
                if val == null:
                    raise TypeError("Option '%s' is empty" % req)

            setattr(obj, opt, val)

    def _startAll(self):
        for pull in self.pulls.values():
            if hasattr(pull, 'started'):
                continue
            pull.started = True
            task.deferLater(reactor, 0, pull.start())

    @api.route('/api/<string:name>', methods=['GET'])
    def api_data(self, request, name):
        if name not in self.pulls:
            return name + ' not exists'
        request.setHeader('content-type', 'application/json')
        return defer.succeed(self.pulls[name].getJson())

    @api.route('/', branch=True)
    def static(self, request):
        return File(self.static_dir)

ep = TheApp(__name__, "OpenCV Pullrequests UI")
