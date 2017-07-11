
import os
import time
import logging
from shutil import rmtree
from user import User
from git import Git

logger = logging.getLogger(__name__)

class Organization(User):

    meta = None

    def update(self):
        self.update_meta()
   
    def gen_rpath(self):
        return "/tmp/safehub/meta-{}-{}".format(self.user, os.getpid())

    def update_meta(self):
        if not os.path.isdir(self.local_path("meta")):
            Git.init(self.local_path("meta"))
        if not self.meta:
            rpath = self.gen_rpath()
            self.meta = Git.clone(self.local_path("meta"), rpath, instantiate=True)
        self.gh.fetch_api(self.user, self.repo, self.meta.cwd)
        self.meta.add()
        self.meta.commit(time.strftime("%Y-%m-%dT%H-%M-%S"))
        self.meta.push()
    
    def local_path(self, part):
        _gen_path = getattr(Organization, "_gen_path")
        return _gen_path(self.base, self.user, self.repo, part)

    def __exit__(self, base, url, token):
        rmtree(self.gen_rpath())
