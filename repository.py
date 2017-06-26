
from urllib.parse import urlparse

def _parse_url(url):
    url_obj = urlparse(url)
    user_repo = url_obj.path.strip("/").strip(".git").split("/")
    if not len(user_repo) == 2:
        raise ValueError("Invalid URL: {}".format(url))
    try:
        return (user_repo[0], user_repo[1])
    except IndexError:
        raise ValueError("Invalid URL: {}".format(url))

def _gen_repo_git_url(user, repo):
    return "https://github.com/{}/{}.git".format(user, repo)

def _gen_wiki_git_url(user, repo):
    return "https://github.com/{}/{}.wiki.git".format(user, repo)

def _gen_path(base, user=None, repo=None, part=None):
    base = base.rstrip("/")
    if user:
        base += "/{}".format(user)
        if repo:
            base += "/{}".format(repo)
            if part:
                base += "/{}.git".format(part)
    return base

class Repository:

    def __init__(self, base, url, token):
        self.base = base
        self.parse_url(url)
        self.init_fs()

    def parse_url(self, url):
        self.user, self.repo = _parse_url(url)

    def init_fs(self):
        if not os.path.isdir(_gen_path(self.base, self.user)):
            os.mkdir(_gen_path(self.base, self.user))
        if not os.path.isdir(_gen_path(self.base, self.user, self.repo)):
            os.mkdir(_gen_path(self.base, self.user, self.repo))

