
from urllib.parse import urlparse
from repository import Repository

class Organization(Repository):

    meta = None

    @classmethod
    def _parse_url(cls, url):
        url_obj = urlparse(url)
        org = url_obj.path.strip("/")
        if "/" in org:
            raise ValueError("Invalid URL: {}".format(url))
        return org

    def connect(self, url):
        self.user = Organization._parse_url(url)
        self.repo = None

    def update(self):
        self.update_meta()
