
import os
import time
from urllib.parse import urlparse

from git import Git
from github import GitHub


class Repository:

    code = None
    wiki = None
    meta = None

    def __init__(self, base, url, token):
        self.base = base
        self.gh = GitHub(token)
        self.connect(url)
        self.init_fs()

    @classmethod
    def _parse_url(cls, url):
        url_obj = urlparse(url)
        user_repo = url_obj.path.strip("/").strip(".git").split("/")
        if not len(user_repo) == 2:
            raise ValueError("Invalid URL: {}".format(url))
        try:
            return (user_repo[0], user_repo[1])
        except IndexError:
            raise ValueError("Invalid URL: {}".format(url))

    @classmethod
    def _gen_code_git_url(cls, user, repo):
        return "git://github.com/{}/{}.git".format(user, repo)

    @classmethod
    def _gen_wiki_git_url(cls, user, repo):
        return "git://github.com/{}/{}.wiki.git".format(user, repo)

    @classmethod
    def _gen_path(cls, base, user=None, repo=None, part=None):
        if part not in ["wiki", "code", "meta", None]:
            raise ValueError("Invalid part: {}".format(part))
        base = base.rstrip("/")
        if user:
            base += "/{}".format(user)
            if repo:
                base += "/{}".format(repo)
                if part:
                    base += "/{}.git".format(part)
            else:
                if part:
                    raise RuntimeError("If part is set, repo must not be None")
        else:
            if repo or part:
                raise RuntimeError("If repo or part is set, user must not be None")
        return base

    def connect(self, url):
        self.user, self.repo = Repository._parse_url(url)

    def init_fs(self):
#        if not os.path.isdir(Repository._gen_path(self.base, self.user)):
#            os.makedirs(Repository._gen_path(self.base, self.user))
        if not os.path.isdir(Repository._gen_path(self.base, self.user, self.repo)):
            os.makedirs(Repository._gen_path(self.base, self.user, self.repo))

    def local_path(self, part):
        _gen_path = getattr(Repository, "_gen_path")
        return _gen_path(self.base, self.user, self.repo, part)

    def _update(self, part):
        repo = getattr(self, part)
        get_path = getattr(Repository, "_gen_{}_git_url".format(part))
        if not os.path.isdir(self.local_path(part)):
            repo = Git.mirror(get_path(self.user, self.repo), self.local_path(part), instantiate=True)
        if not repo:
            repo = Git(self.local_path(part))
        repo.fetch()

    def update_code(self):
        self._update("code")

    def update_wiki(self):
        self._update("wiki")

    def update_meta(self):
        if not os.path.isdir(self.local_path("meta")):
            Git.init(self.local_path("meta"))
        if not self.meta:
            rpath = "/tmp/safehub/meta-{}".format(os.getpid())
            self.meta = Git.clone(self.local_path("meta"), rpath, instantiate=True)
        self.gh.fetch_api(self.user, self.repo, self.meta.cwd)
        self.meta.add()
        self.meta.commit(time.strftime("%Y-%m-%dT%H-%M-%S"))
        self.meta.push()

    
    def update(self):
        self.update_code()
        self.update_wiki()
        self.update_meta()

