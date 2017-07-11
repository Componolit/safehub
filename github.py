
import os
import json
import requests

class TemporaryError(Exception):
    def __init__(self, message=""):
        super(TemporaryError, self).__init__(message)
        self.message = message

class GitHubBase:

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
                data = self.get_data(user, repo, path + f + "?state=all")
                with open(cwd + path + f + ".json", 'w') as df:
                    json.dump(data, df)
                raw[f] = data
            except TemporaryError as e:
                print(e)
        return raw


class GitHub(GitHubBase):

    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({'Authorization': 'token {}'.format(token)})
        self.base_url = "https://api.github.com/"

    def _get(self, url):
        print(url)
        try:
            response = self.session.get(url)
        except requests.exceptions.ConnectionError:
            raise TemporaryError
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise TemporaryError("{}: {}, {}".format(response.url, response.status_code, str(e)))
        return response.content.decode('utf-8'), response.headers

    def get_data(self, user, repo, path):
        return self.gen_data("/".join(p for p in [self.base_url.strip("/"),
                                       "repos" if repo else "orgs",
                                       user.strip("/"),
                                       repo.strip("/") if repo else "",
                                       path.strip("/")] if p != ""))

    def fetch_api(self, user, repo, cwd):
        if repo:
            repo_json = self.fetch_repository(user, repo, cwd, "/", ["collaborators", "comments", "keys", "forks", "pulls", "issues", "labels", "milestones"])
            if "pulls" in repo_json:
                for pull in repo_json["pulls"]:
                    pulls = self.fetch_repository(user, repo, cwd, "/pulls/{}/".format(pull["number"]), ["reviews", "comments", "requested_reviewers"])
            if "issues" in repo_json:
                for issue in repo_json["issues"]:
                    issues = self.fetch_repository(user, repo, cwd, "/issues/{}/".format(issue["number"]), ["comments", "events", "labels"])
        else:
            org_json = self.fetch_repository(user, repo, cwd, "/", ["members", "outside_collaborators", "teams", "hooks"])

    def fetch_repositories(self, user):
        return self.gen_data("/".join([self.base_url.strip("/"), "users", user, "repos"]))

    def get_repo_data(self, user, repo):
        return self.gen_data("/".join([self.base_url.strip("/"), "repos", user, repo]))
