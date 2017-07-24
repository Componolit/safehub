
import os
import logging
from urllib.parse import urlparse
from pathlib import Path
from github import GitHub

logger = logging.getLogger(__name__)

class User:

    def __init__(self, base, url, token):
        self.base = base
        self.gh = GitHub(token)
        self.connect(url)
        self.init_fs()

    @classmethod
    def _parse_url(cls, url):
        url_obj = urlparse(url)
        org = url_obj.path.strip("/")
        if "/" in org:
            raise ValueError("Invalid URL: {}".format(url))
        return org
    
    def init_fs(self):
        if not os.path.isdir(User._gen_path(self.base, self.user, self.repo)):
            os.makedirs(User._gen_path(self.base, self.user, self.repo))
    
    @classmethod
    def _gen_path(cls, base, user=None, repo=None, part=None):
        if part not in ["wiki", "code", "meta", None]:
            raise ValueError("Invalid part: {}".format(part))
        base = Path(base)
        if user:
            base /= "{}".format(user)
            if repo:
                base /= "{}".format(repo)
                if part:
                    base /= "{}.git".format(part)
            else:
                if part == "meta":
                    base /= "{}.git".format(part)
                elif part:
                    raise RuntimeError("If part is set and not meta, repo must not be None")
        else:
            if repo or part:
                raise RuntimeError("If repo or part is set, user must not be None")
        return str(base)

    def connect(self, url):
        self.user = User._parse_url(url)
        self.repo = None

    def get_repositories(self):
        repos = self.gh.fetch_repositories(self.user)
        return [repo["html_url"] for repo in repos]

    def __enter__(self):
        return self
    
    def __exit__(self, base, url, token):
        pass
