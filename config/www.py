import copy, simplejson as json

from buildbot.plugins import util

from builders import BuilderNamesByCompiler
from codebases import Codebases

def filter_pr(pr):
    if pr['base_branch'] not in ['master', '3.4']:
        print("Unsupported branch " + pr['base_branch'])
        return False
    return True

#### Pullrequests plugin
opencv = dict(
    name='opencv',
    user='opencv',
    repo='opencv',
    caption='Pull Requests(OpenCV)',
    icon='eye',
    codebases=Codebases.genBases(),
    filter_pr=filter_pr,
    config_prefix='pw_',
    config=dict(
        compilers=dict(type='builders', default=['gcc-5', 'power9_gcc-6'], search=BuilderNamesByCompiler),
        with_opencv=dict(type='sourcestamp', name='opencv', codebase='opencv_merge', default={}),
        with_opencv_contrib=dict(type='sourcestamp', name='opencv_contrib', codebase='opencv_contrib_merge'),
        with_opencv_extra=dict(type='sourcestamp', name='opencv_extra', codebase='opencv_extra_merge'),
        build_type=dict(default='release'),
        cmake_definitions={},
        disable_tests=dict(default='rgbd, shape'),
        disable_perf_tests=dict(default='stereo, tracking'),
        filter_tests={},
        filter_perf_tests={}
    )
)

contrib = copy.deepcopy(opencv)
contrib['config']['with_opencv'].pop('default')
contrib['config']['with_opencv_contrib']['default'] = {}
contrib.update(dict(
    name='opencv_contrib',
    repo='opencv_contrib',
    caption='Pull Requests(Contrib)',
    icon='share-alt'
))

### Fetch users from json file
users  = []
admins = []
for user in json.load(open('../users.json')):
    if user['admin']:
        admins.append(user['user'])
    users.append((user['user'], user['pass']))

authz = util.Authz(
    allowRules = [
        util.AnyEndpointMatcher(role='admins', defaultDeny=False),
        util.StopBuildEndpointMatcher(role='owner'),
        util.ForceBuildEndpointMatcher(role='users'),
        util.ForceBuildEndpointMatcher(role='users'),
        util.ForceBuildEndpointMatcher(role='users'),
        util.AnyControlEndpointMatcher(role='admins')
    ],
    roleMatchers = [
        util.RolesFromUsername(roles=['admins'], usernames=admins),
        util.RolesFromUsername(roles=['users'], usernames=users),
        util.RolesFromOwner(role='owner')
    ]
)

######################################################################

WWW = dict(
    port=8010, authz=authz, auth=util.UserPasswordAuth(users),
    plugins=dict(console_view={}, pullrequests=[opencv, contrib])
)
