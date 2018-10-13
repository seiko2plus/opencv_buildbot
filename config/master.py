import re
from buildbot.plugins import *

from schedulers import Schedulers
from builders import Builders
from workers import Workers
from codebases import Codebases
from www import WWW

c = BuildmasterConfig = {}
c['title'] = "Open Source Computer Vision Library"
c['titleURL'] = "https://opencv.org/"
c['buildbotURL'] = "https://ocv-power.imavr.com/"
c['change_source'] = []
c['protocols'] = {'pb': {'port': 9989}}
c['db'] = dict(db_url='sqlite:///state.sqlite')

c['schedulers'] = Schedulers
c['builders'] = Builders
c['workers']  = Workers
c['codebaseGenerator'] = Codebases.generator
c['www'] = WWW

####### Caches

c['caches'] = {
    'Changes' : 100,
    'Builds' : 500,
    'chdicts' : 100,
    'BuildRequests' : 10,
    'SourceStamps' : 20,
    'ssdicts' : 20,
    'objectids' : 10,
    'usdicts' : 100,
}