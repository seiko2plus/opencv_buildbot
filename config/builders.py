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
            codebases=Codebases.repos
        ),
    ]: Builders.append(builder); BuilderNames.append(builder.name); BuilderNamesByCompiler[ver] = builder.name