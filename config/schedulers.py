from buildbot.schedulers.forcesched import ForceScheduler, NestedParameter, StringParameter, ChoiceStringParameter
from buildbot.util import *
from buildbot.schedulers.timed import Nightly

from codebases import Codebases
from builders import BuilderNames

Schedulers = []
Schedulers.append(ForceScheduler(
	name='force',
	builderNames=BuilderNames,
	codebases=Codebases.genBaseParameters() + Codebases.genMergeBaseParameters(),
	properties=[
        ChoiceStringParameter(
            name='build_type', label='build type',
            choices=['debug', 'release'], default='release'
        ),
        StringParameter(name='cmake_definitions', label='cmake definitions', default=''),
        StringParameter(name='disable_tests', label='disable accuracy tests', default='java, rgbd, shape'),
        StringParameter(name='disable_perf_tests', label='disable performance tests', default='stereo, tracking'),
        StringParameter(name='filter_tests', label='filter accuracy tests', default=''),
        StringParameter(name='filter_perf_tests', label='filter performance tests', default='')
    ]
))

for b in Codebases.branches:
    bases = Codebases.genBases(branch=b)
    for bdt in ['debug', 'release']:
        Schedulers.append(Nightly(
            name="nightly %s-%s" % (bdt, b),
            hour=3,
            builderNames=BuilderNames,
            codebases=bases,
            properties=dict(
                build_type=bdt,
                disable_tests='java, rgbd, shape',
                disable_perf_tests='stereo, tracking'
            )
        ))