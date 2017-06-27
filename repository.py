
from urllib.parse import urlparse
from github import Github

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

class Repository:

    def __init__(self, base, url, token):
        self.base = base
        self.gh = Github(token)
        self.connect(url)
        self.init_fs()

    def connect(self, url):
        user, repo = _parse_url(url)
        self.user = gh.get_user(user)
        self.repo = self.user.get_repo(repo)

    def init_fs(self):
        if not os.path.isdir(_gen_path(self.base, self.user.login)):
            os.mkdir(_gen_path(self.base, self.user.login))
        if not os.path.isdir(_gen_path(self.base, self.user.login, self.repo.name)):
            os.mkdir(_gen_path(self.base, self.user.login, self.repo.name))

