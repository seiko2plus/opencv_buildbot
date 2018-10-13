from buildbot.util import giturlparse
from buildbot.schedulers.forcesched import CodebaseParameter, ChoiceStringParameter, FixedParameter

class NewCodebases:
    def __init__(self, **kwargs):
        self.owner = kwargs.pop('owner', 'opencv')
        self.repos = kwargs.pop('repos', ['opencv', 'opencv_contrib', 'opencv_extra'])
        self.branches = kwargs.pop('branches', ['master', '3.4'])
        self.baseURL = kwargs.pop('baseURL', 'http://code.ocv')
        if self.baseURL.endswith('/'):
            self.baseURL = self.baseURL[:-1]

    def generator(self, chdict):
        repourl = giturlparse(chdict['repository'])
        if repourl.owner == self.owner and repourl.repo in self.repos:
            return repourl.repo
        return None

    def genRepoURL(self, url, owner, repo):
        if url is None:
            return ''
        return "%s/%s/%s" % (url, owner, repo)

    def genBases(self, **kwargs):
        branch = kwargs.pop('branch', None)
        revision = kwargs.pop('revision', None)
        prefix = kwargs.pop('prefix', '')
        repos = kwargs.pop('repos', self.repos)
        url = kwargs.pop('url', self.baseURL)
        owner = kwargs.pop('owner', self.owner)
        bases = {}
        for repo in repos:
            bases[repo + prefix] = {
                'repository': self.genRepoURL(url, owner, repo),
                'branch': branch,
                'revision': revision
            }
        return bases

    def genBaseParameters(self, **kwargs):
        repos = kwargs.pop('repos', self.repos)
        branches = kwargs.pop('branches', self.branches)
        parms = []
        for repo in repos:
            parms.append(CodebaseParameter(
                codebase=repo,
                label=repo,
                branch=ChoiceStringParameter(
                    name='branch',
                    choices=self.branches,
                    default=self.branches[0]
                ),
                repository=FixedParameter(name='repository', default=self.genRepoURL(self.baseURL, self.owner, repo)),
                project=FixedParameter(name='project', default='')
            ))
        return parms

    def genMergeBaseParameters(self, **kwargs):
        repos = kwargs.pop('repos', self.repos)
        branches = kwargs.pop('branches', self.branches)
        parms = []
        for repo in repos:
            parms.append(CodebaseParameter(
                codebase=repo + '_merge',
                label="Merge %s with test branch" % repo,
                project=FixedParameter(name='project', default='')
            ))
        return parms

    def genBrnachStamps(self, branch, prefix=''):
        stamps = []
        for repo in self.repos:
            stamps.append({
                'codebase': repo + prefix,
                'branch': branch
            })
        return stamps

Codebases = NewCodebases()