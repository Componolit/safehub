
import os
import json
import requests

class TemporaryError(Exception):
    def __init__(self, message=""):
        super(TemporaryError, self).__init__(message)
        self.message = message

class FatalError(Exception):
    def __init__(self, message=""):
        super(FatalError, self).__init__(message)
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
            os.mkdir(cwd + path)
        for f in files:
            try:
                data = self.get_data(user, repo, path + f)
                with open(cwd + path + f, 'w') as df:
                    json.dump(data, df)
                raw[f] = data
            except TemporaryError:
                pass
        return data


class GitHub(GitHubBase):

    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({'Authorization': 'token {}'.format(token)})
        self.base_url = "https://api.github.com/repos/"

    def _get(self, url):
        try:
            response = self.session.get(url)
        except requests.exceptions.ConnectionError:
            raise TemporaryError
        response.raise_for_status()
        if response.status_code != 200:
            if response.status_code >= 500:
                raise TemporaryError("{}: {}".format(response.url, response.status_code))
            else:
                raise FatalError("{}: {}".format(response.url, response.status_code))
        return response.content.decode('utf-8'), response.headers

    def get_data(self, user, repo, path):
        return self.gen_data("/".join([self.base_url.strip("/"),
                                       user.strip("/"),
                                       repo.strip("/"),
                                       path.strip("/")]))

    def fetch_api(self, user, repo, cwd):
        repo = self.fetch_repository(user, repo, cwd, "/", ["collaborators", "comments", "keys", "forks", "pulls"])
        if "pulls" in repo:
            for pull in repo["pulls"]:
                pulls = self.fetch_repository(user, repo, cwd, "/pulls/{}/".format(pull["id"]), ["reviews", "comments", "requested_reviewers"])
                print(pulls)
