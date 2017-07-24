
import os
import json
import time
import logging
import requests

logger = logging.getLogger(__name__)

class TemporaryError(Exception):
    def __init__(self, message=""):
        super(TemporaryError, self).__init__(message)
        self.message = message

class RateLimitExceeded(Exception):
    def __init__(self, message=""):
        super(RateLimitExceeded, self).__init__(message)
        self.message = message

class GitHubBase:

    base_url = "https://api.github.com/"
    token = None

    def _get(self, url):
        raise NotImplementedError

    @classmethod
    def _parse_link(cls, link):
        items = link.strip(",").split(",")
        data = {}
        for item in items:
            i = item.split(";")
            data[i[1].split("=")[1].strip("\"")] = i[0].strip("< >")
        return (data["first"] if "first" in data else None,
                data["last"] if "last" in data else None,
                data["next"] if "next" in data else None,
                data["prev"] if "prev" in data else None)

    def gen_data(self, url):
        raise NotImplementedError

    def _gen_data(self, url):
        content, headers = self._get(url)
        data = json.loads(content)
        if "Link" in headers:
            nxt = self._parse_link(headers["Link"])[2]
            while nxt:
                content, headers = self._get(nxt)
                nxt = self._parse_link(headers["Link"])[2]
                data.extend(json.loads(content))
        return data

    def get_data(self, user, repo, path):
        raise NotImplementedError
        
    def fetch_repository(self, user, repo, cwd, path, files):
        raw = {}
        if not os.path.isdir(cwd + path):
            os.makedirs(cwd + path)
        for f in files:
            try:
                data = self.get_data(user, repo, path + f + "?per_page=100" if f else "" + ("&state=all" if f in ["issues", "pulls"] else ""))
                if not f:
                    f = repo
                with open(cwd + path + f + ".json", 'w') as df:
                    json.dump(data, df, sort_keys=True, indent=4)
                raw[f] = data
            except TemporaryError as e:
                logger.warning(str(e))
        return raw

    def _get_data(self, user, repo, path):
        return self.gen_data("/".join(p for p in [self.base_url.strip("/"),
                                       "repos" if repo else "orgs",
                                       user.strip("/"),
                                       repo.strip("/") if repo else "",
                                       path.strip("/")] if p != ""))

    def fetch_repositories(self, user):
        return self.gen_data("/".join([self.base_url.strip("/"), "users", user, "repos"]))

    def get_repo_data(self, user, repo):
        return self.gen_data("/".join([self.base_url.strip("/"), "repos", user, repo]))

class GitHub(GitHubBase):

    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({'Authorization': 'token {}'.format(token)})

    def get_data(self, user, repo, path):
        return self._get_data(user, repo, path)

    def _get(self, url):
        try:
            response = self.session.get(url)
        except requests.exceptions.ConnectionError:
            raise TemporaryError
        if "X-RateLimit-Remaining" in response.headers:
            if int(response.headers["X-RateLimit-Remaining"]) < 10:
                sleeptime = int(int(response.headers["X-RateLimit-Reset"]) - time.time()) + 5
                logger.warning("RateLimit nearly depleted, waiting {}s to get new resources".format(sleeptime))
                time.sleep(sleeptime)
                if int(response.headers["X-RateLimit-Remaining"]) == 0:
                    return self._get(url)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if "X-RateLimit-Remaining" in response.headers:
                if int(response.headers["X-RateLimit-Remaining"]) == 0:
                    raise RateLimitExceeded(response.headers["X-RateLimit-Reset"])
            logger.debug(response.content.decode('utf-8'))
            raise TemporaryError("{}: {}, {}".format(response.url, response.status_code, str(e)))
        return response.content.decode('utf-8'), response.headers

    def gen_data(self, url):
        return self._gen_data(url)

    def fetch_api(self, user, repo, cwd):
        if repo:
            repo_json = self.fetch_repository(user, repo, cwd, "/", ["", "collaborators", "comments", "keys", "forks", "pulls", "issues", "labels", "milestones"])
            if "pulls" in repo_json:
                for pull in repo_json["pulls"]:
                    pulls = self.fetch_repository(user, repo, cwd, "/pulls/{}/".format(pull["number"]), ["reviews", "comments", "requested_reviewers"])
            if "issues" in repo_json:
                for issue in repo_json["issues"]:
                    issues = self.fetch_repository(user, repo, cwd, "/issues/{}/".format(issue["number"]), ["comments", "events", "labels"])
        else:
            org_json = self.fetch_repository(user, repo, cwd, "/", ["members", "outside_collaborators", "teams", "hooks"])

