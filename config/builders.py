from factory.builder import Builder
from workers   import WorkerTags
from compilers import LinuxCompilers
from codebases import Codebases

Builders = []
BuilderNames = []
BuilderNamesByCompiler = {}

for ver, env in LinuxCompilers.items():
    for builder in [
        Builder(
            name="Power8 Linux(%s) %s" % (ver, Codebases.owner),
            compiler=env,
            workernames=WorkerTags['pullrequests'],
            cmake_definitions=dict(WITH_EIGEN='OFF') if ver.startswith('clang') else {},
            codebases=Codebases.repos
        )
    ]: Builders.append(builder); BuilderNames.append(builder.name); BuilderNamesByCompiler[ver] = builder.name

for ver, env in LinuxCompilers.items():
    for builder in [
        Builder(
            name="Power9 Linux(%s) %s" % (ver, Codebases.owner),
            compiler=env,
            workernames=WorkerTags['power9_pullrequests'],
            cmake_definitions=dict(WITH_EIGEN='OFF') if ver.startswith('clang') else {},
            force_cmake_definitions=dict(CPU_BASELINE='VSX3'),
            codebases=Codebases.repos
        )
    ]: Builders.append(builder); BuilderNames.append(builder.name); BuilderNamesByCompiler['power9_' + ver] = builder.name
