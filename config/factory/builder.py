import re
from twisted.internet.defer import inlineCallbacks as callback, returnValue

from buildbot.config import BuilderConfig

from buildbot.status.builder import SUCCESS, FAILURE

from buildbot.process.logobserver import BufferLogObserver
from buildbot.process.buildstep import ShellMixin, BuildStep
from buildbot.process.factory import BuildFactory
from buildbot.process.properties import Interpolate, Property, renderer

from buildbot.steps.source.git import Git
from buildbot.steps.cmake import CMake
from buildbot.steps.shell import Compile, Configure, ShellCommand, SetPropertyFromCommand
from buildbot.steps.worker import RemoveDirectory, MakeDirectory

from buildbot.plugins import util

from .command_test_cpp import CommandTestCPP
from .command_test_java import CommandTestJava
from .command_test_py import CommandTestPy


class DetermineTests(ShellMixin, BuildStep):
    def __init__(self, **kwargs):
        kwargs = self.setupShellMixin(kwargs)
        BuildStep.__init__(self, **kwargs)
        self.observer = BufferLogObserver(wantStdout=True, wantStderr=True)
        self.addLogObserver('stdio', self.observer)

    @callback
    def run(self):
        cmd = yield self.makeRemoteShellCommand()
        yield self.runCommand(cmd)

        result = cmd.results()
        if result == 0:
            tests = self.extract_tests(self.observer.getStderr())

            is_opencv = self.is_merge_with('opencv')
            is_contrib = self.is_merge_with('opencv_contrib')

            if is_opencv and not is_contrib:
                self.add_tests(tests['tests_performance_main'], True)
                self.add_tests(tests['tests_accuracy_main'])
            elif is_contrib and not is_opencv:
                self.add_tests(self.tests_not_mainly(tests, 'tests_performance'), True)
                self.add_tests(self.tests_not_mainly(tests, 'tests_accuracy'))
            else:
                self.add_tests(tests['tests_performance'], True)
                self.add_tests(tests['tests_accuracy'])

        returnValue(result)

    def tests_not_mainly(self, tests, key):
        return [i for i in tests[key] if i not in tests[key + '_main']]

    def is_merge_with(self, repo):
        stamp = self.build.getSourceStamp(repo + '_merge')
        return (stamp is not None) and (stamp.repository != '')

    def extract_tests(self, stderr):
        tests = {
            'tests_accuracy': [],
            'tests_performance': [],
            'tests_accuracy_main': [],
            'tests_performance_main': []
        }
        props_list = stderr.split(':')
        for i in range(1, len(props_list), 2):
            tests[props_list[i]] = props_list[i + 1].split()
        return tests

    def filter_tests(self, tests_list, perf):
        prefix = '_perf_' if perf else '_'

        disabled_tests = []
        disabled_str = self.getProperty("disable%stests" % prefix)
        if disabled_str is not None:
            disabled_str = re.sub(r"\s+", '', disabled_str)
            if disabled_str == '*':
                return {}
            disabled_tests = disabled_str.split(',')

        enable_all = False
        filter_dict = {}
        filter_str = self.getProperty("filter%stests" % prefix)
        if filter_str is not None:
            filter_list = re.sub(r"\s+", '', filter_str).split(',')
            for gfilter in filter_list:
                filter_item = gfilter.split(':')
                name = filter_item[0]
                if not name:
                    continue
                if len(filter_item) == 1:
                    if name == '*':
                        enable_all = True
                        continue
                    filter_dict[name] = '*'
                elif len(filter_item) == 2:
                    filter_dict[name] = filter_item[1]

        if len(filter_dict) == 0:
            enable_all = True

        tests = {}
        for test in tests_list:
            if test in disabled_tests:
                continue
            filter_test = filter_dict.pop(test, None)
            if filter_test is not None:
                tests[test] = filter_test
            elif enable_all:
                tests[test] = '*'
        return tests


    def add_tests(self, tests_list, perf=False):
        steps = []
        tests = self.filter_tests(tests_list, perf)

        for test in sorted(tests.keys()):
            gfilter = tests[test]
            prefix = 'perf' if perf else 'test'
            argsc = dict(
                name="%s %s" % (prefix, test),
                command=None,
                env={
                    'OPENCV_TEST_DATA_PATH': Interpolate('%(prop:builddir)s/opencv_extra/testdata')
                },
                logfiles=None, timeout=20 * 60, maxTime=60 * 60
            )
            step = None
            if test.startswith('python'):
                if test == 'python3':
                    argsc['env']['PYTHONPATH'] = Interpolate('%(prop:builddir)s/build/lib/python3')
                elif test == 'python2':
                    argsc['env']['PYTHONPATH'] = Interpolate('%(prop:builddir)s/build/lib')

                argsc['env']['PYTHONDONTWRITEBYTECODE'] = '1'
                argsc['env']['PYTHONUNBUFFERED'] = '1'

                argsc['command'] = [
                    test, '../opencv/modules/python/test/test.py --repo ../opencv -v 2>&1'
                ]
                step = CommandTestPy
            else:
                argsc['command'] = [
                    'python2 ../opencv/modules/ts/misc/run.py -t', test
                ]

                if test == 'java':
                    step = CommandTestJava
                    argsc['command'].append('--gtest_output=xml:results_test_java.xml')
                else:
                    step = CommandTestCPP

                if perf:
                    argsc['command'].append('--check --perf_impl=plain')
                    argsc['command'].append("--gtest_output=xml:results_%s_%s.xml" % (prefix, test))
                    argsc['logfiles']={'results': "results_%s_%s.xml" % (prefix, test)}
                else:
                    argsc['command'].append('-a')

                argsc['command'].append("--gtest_filter=%s" % gfilter)

            argsc['command'] = ' '.join(argsc['command'])
            steps.append(step(**argsc))

        self.build.addStepsAfterCurrentStep(steps)


class Builder(BuilderConfig):
    factory = None

    def __init__(self, **kwargs):
        self.name = kwargs.pop('name', None)
        self.workers = kwargs.pop('workernames', [])
        self.codebases = kwargs.pop('codebases', [])
        self.arch = kwargs.pop('arch', 'ppc64le')
        self.os = kwargs.pop('os', 'linux')
        self.compiler = kwargs.pop('compiler', None)
        self.steps = kwargs.pop('steps', [])
        self.cmake_definitions = kwargs.pop('cmake_definitions', {})
        # override property cmake_definitions
        self.force_cmake_definitions = kwargs.pop('force_cmake_definitions', {})
        self.factory = BuildFactory()
        BuilderConfig.__init__(self,
            name=self.name, workernames=self.workers,
            factory=self.getSteps(), properties=kwargs.pop('properties', {})
        )

    def addStep(self, step):
        self.factory.addStep(step)

    def getSteps(self):
        self.stepCleanupBuild()
        self.stepSources()
        self.stepCmake()
        self.stepCompile()
        self.stepDetermineTests()
        for step in self.steps:
            self.addStep(step)
        return self.factory

    def stepCleanupBuild(self):
        # workaround, buildbot immediate terminate launched processes(SIGKILL),
        # git has no chance for proper cleanup of .lock files
        for base in self.codebases:
            self.addStep(ShellCommand(
                name="Remove git locks " + base,
                command='rm -f .git/index.lock',
                workdir=base,
                hideStepIf=lambda result, s: result == SUCCESS,
                haltOnFailure=True
            ))
        self.addStep(RemoveDirectory(
            dir='build', hideStepIf=lambda result, s: result == SUCCESS,
            haltOnFailure=True
        ))
        self.addStep(MakeDirectory(
            dir='build', hideStepIf=lambda result, s: result == SUCCESS,
            haltOnFailure=True
        ))

    def stepSources(self):
        for base in self.codebases:
            self.addStep(Git(
                name='Fetch ' + base, workdir=base,
                repourl = Interpolate("%%(src:%s:repository)s" % base),
                codebase=base, mode='full', method='clean',
                retryFetch=True, retry=(300, 5), haltOnFailure=True,
                getDescription={'always': True},
            ))

        def dostep_if(base):
            def dostep_fn(step):
                stamp = step.build.getSourceStamp(base + '_merge')
                return (stamp is not None) and (stamp.repository != '')
            return dostep_fn

        for base in self.codebases:
            self.addStep(ShellCommand(
                name="Merge %s with test branch" % base,
                command=Interpolate('git pull -v "%%(src:%s_merge:repository)s" "%%(src:%s_merge:branch)s"'
                    % (base, base)),
                workdir=base, description='merge ' + base, descriptionDone='merge ' + base,
                doStepIf=dostep_if(base), haltOnFailure=True
            ))

    def stepCmake(self):
        @renderer
        def init_cmake_definitions(props):
            defs = {}
            defs['BUILD_SHARED_LIBS'] = 'ON'
            defs['BUILD_EXAMPLES'] = 'ON'
            defs['BUILD_TESTS'] = 'ON'
            defs['BUILD_PERF_TESTS'] = 'ON'
            defs['OPENCV_ENABLE_NONFREE'] = 'ON'
            defs['WITH_OPENCL'] = 'OFF'
            defs['PYTHON_DEFAULT_EXECUTABLE'] = '/usr/bin/python3'

            if self.compiler is not None:
                defs["CMAKE_C_COMPILER"] = self.compiler['CC']
                defs["CMAKE_CXX_COMPILER"] = self.compiler['CXX']

            defs['OPENCV_EXTRA_MODULES_PATH'] = props.getProperty('builddir') + '/opencv_contrib/modules'
            defs.update(self.cmake_definitions)

            extra = {}
            cdef_str = props.getProperty('cmake_definitions', None)
            if cdef_str is None:
                defs.update(self.force_cmake_definitions)
                return defs

            cdef_list = re.sub(r"\s+", '', cdef_str).split(',')
            for cdef in cdef_list:
                name_val = cdef.split(':')
                name_val_len = len(name_val)
                if name_val_len != 2:
                    continue

                val = name_val[1]
                """
                if val == '1':
                    val = 'ON'
                elif val != 'ON':
                    val = 'OFF'
                """
                name = name_val[0]
                if name == 'OPENCV_EXTRA_MODULES_PATH':
                    if val == 'OFF':
                        defs.pop(name)
                else:
                    extra[name] = val

            defs.update(extra)
            defs.update(self.force_cmake_definitions)
            return defs

        self.addStep(CMake(
            name="cmake", descriptionDone='cmake', description='cmake',
            path="../opencv", definitions=init_cmake_definitions,
            lazylogfiles=True, warnOnWarnings=True, haltOnFailure=True,
            logfiles=dict(
                CMakeOutput='CMakeFiles/CMakeOutput.log',
                CMakeError='CMakeFiles/CMakeError.log',
                cache='CMakeCache.txt', vars='CMakeVars.txt'
            )
        ))

    def stepCompile(self):
        @renderer
        def compile_command(props):
            build_cpus = props.getProperty('parallel', 2)
            build_type = props.getProperty('build_type', 'release')
            command = 'cmake --build . --config %s -- -j%d' % (build_type, build_cpus)
            return command

        @renderer
        def compile_desc(props):
            return 'compile ' + props.getProperty('build_type', 'release')

        self.addStep(Compile(
            name=compile_desc, descriptionDone=compile_desc, description=compile_desc,
            command=compile_command, warnOnWarnings=True, haltOnFailure=True
        ))

    def stepDetermineTests(self):
        exe = 'python2 ../opencv/modules/ts/misc/run.py'
        props = {
            'tests_performance': '--list_short',
            'tests_accuracy': '--list_short -a',
            'tests_performance_main': '--list_short_main',
            'tests_accuracy_main': '--list_short_main -a'
        }

        commands = []
        for p, arg in props.items():
            commands.append('>&2 echo ":%s:"' % p)
            commands.append("%s %s" % (exe, arg))

        self.addStep(DetermineTests(
            name='Determine tests',
            description='Determine tests',
            descriptionDone='Determine tests',
            command=' && '.join(commands),
            haltOnFailure=True
        ))
