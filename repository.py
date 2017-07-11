
import os
import re
import logging
from urllib.parse import urlparse

from organization import Organization
from git import Git

logger = logging.getLogger(__name__)

class Repository(Organization):

    code = None
    wiki = None
    meta = None

    def gen_rpath(self):
        return "/tmp/safehub/meta-{}-{}-{}".format(self.user, self.repo, os.getpid())

    @classmethod
    def _parse_url(cls, url):
        url_obj = urlparse(url)
        user_repo = re.sub('\.git$', '', url_obj.path.strip("/")).split("/")
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

    def get_github_url(self):
        return "https://github.com/{}/{}".format(self.user, self.repo)

    def connect(self, url):
        self.user, self.repo = Repository._parse_url(url)

    def _update(self, part):
        repo = getattr(self, part)
        get_path = getattr(Repository, "_gen_{}_git_url".format(part))
        if not os.path.isdir(self.local_path(part)):
            try:
                repo = Git.mirror(get_path(self.user, self.repo), self.local_path(part), instantiate=True)
            except RuntimeError as e:
                logger.warn("Failed to clone repository: ".format(str(e)))
                return
        if not repo:
            repo = Git(self.local_path(part))
        repo.fetch()

    def update_code(self):
        self._update("code")

    def update_wiki(self):
        self._update("wiki")


    
    def update(self):
        self.update_code()
        self.repo_data = self.gh.get_repo_data(self.user, self.repo)
        if self.repo_data["has_wiki"]:
            self.update_wiki()
        self.update_meta()

